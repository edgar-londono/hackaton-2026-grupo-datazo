(() => {
  const picker = document.getElementById("property-picker");
  const view = document.getElementById("property-view");
  const formatter = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
  const areaFormatter = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });
  let equipmentMap = null;
  let facilityMarkers = new Map();
  let include4375000 = true;
  const facilityPalette = {
    educacion: { fill: "#a9c8e8", stroke: "#557caa" },
    salud: { fill: "#e8b0b7", stroke: "#9b5d68" },
    parques: { fill: "#a9d2b1", stroke: "#5b8b65" },
    abastecimiento: { fill: "#efd28f", stroke: "#9a7739" },
    seguridad: { fill: "#bcb0e5", stroke: "#75649d" },
    cultura: { fill: "#dcb2dc", stroke: "#8d648d" },
    default: { fill: "#c2cdd0", stroke: "#66777b" }
  };
  const money = (value) => value == null ? "Datos insuficientes" : `COP ${formatter.format(value)}`;
  const text = (value, fallback = "No disponible") => value == null || value === "" ? fallback : value;
  const list = (value) => Array.isArray(value) ? value : [];
  const labels = {
    abastecimiento: "Abastecimiento",
    buenos_aires_el_salvador: "Buenos Aires / El Salvador",
    castellana_laureles: "La Castellana / Laureles",
    ditaires_itagui: "Ditaires, Itagüí",
    educacion: "Educación",
    cultura: "Cultura",
    parques: "Parques",
    por_remodelar: "Por remodelar",
    remodelado: "Remodelado",
    remodelada: "Remodelada",
    seguridad: "Seguridad",
    salud: "Salud",
    sin_clasificar: "Sin clasificar",
    sin_remodelar_obra_negra: "Sin remodelar (obra negra)"
  };
  const missingLabels = {
    coordenadas_exactas: "Coordenadas exactas",
    direccion: "Dirección",
    fecha_publicacion_comparables: "Fecha de publicación de anuncios comparables",
    precios_de_cierre: "Precios de cierre"
  };
  const labelCase = (value) => {
    const source = text(value);
    const key = source.toLocaleLowerCase("es-CO").replaceAll(" ", "_");
    if (labels[key]) return labels[key];
    const readable = source.replaceAll("_", " ").toLocaleLowerCase("es-CO");
    return readable.charAt(0).toLocaleUpperCase("es-CO") + readable.slice(1);
  };
  const municipality = (value) => ({ medellin: "Medellín", itagui: "Itagüí" }[value] || labelCase(value));
  const displayId = (id) => `Inmueble ${String(id).match(/\d+$/)?.[0] || id}`;
  const facilityColor = (category) => facilityPalette[category] || facilityPalette.default;

  function directionsUrl(origin, destination) {
    const url = new URL("https://www.google.com/maps/dir/");
    url.searchParams.set("api", "1");
    url.searchParams.set("origin", `${origin.lat},${origin.lon}`);
    url.searchParams.set("destination", `${destination.lat},${destination.lon}`);
    url.searchParams.set("travelmode", "walking");
    return url.href;
  }

  function osmUrl(id) {
    if (typeof id !== "string" || !/^(node|way|relation)\/\d+$/.test(id)) return null;
    return `https://www.openstreetmap.org/${id}`;
  }

  function row(label, value) {
    const item = document.createElement("div");
    item.className = "detail-row";
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    item.append(term, description);
    return item;
  }

  function stat(value, label) {
    const item = document.createElement("div");
    item.className = "stat";
    const number = document.createElement("b");
    number.textContent = value;
    const caption = document.createElement("span");
    caption.textContent = label;
    item.append(number, caption);
    return item;
  }

  function popupContent(titleText, categoryText, feature, origin) {
    const content = document.createElement("div");
    content.className = "map-popup";
    const title = document.createElement("strong");
    title.textContent = titleText;
    content.append(title);
    if (categoryText) {
      const category = document.createElement("span");
      const categoryLabel = document.createElement("strong");
      categoryLabel.textContent = "Tipo: ";
      category.append(categoryLabel, `${categoryText}.`);
      content.append(category);
    }
    const point = feature?.geometry?.coordinates;
    if (origin && Array.isArray(point) && point.length === 2 && point.every(Number.isFinite)) {
      const routeLink = document.createElement("a");
      routeLink.href = directionsUrl(origin, { lon: point[0], lat: point[1] });
      routeLink.target = "_blank";
      routeLink.rel = "noopener noreferrer";
      const routeLabel = document.createElement("strong");
      routeLabel.textContent = "Ver en: ";
      routeLink.append(routeLabel, "Google Maps");
      content.append(routeLink);
    }
    const source = osmUrl(feature?.properties?.osm_id);
    if (source) {
      const sourceLink = document.createElement("a");
      sourceLink.href = source;
      sourceLink.target = "_blank";
      sourceLink.rel = "noopener noreferrer";
      const sourceLabel = document.createElement("strong");
      sourceLabel.textContent = "Ver en: ";
      sourceLink.append(sourceLabel, "OpenStreetMap");
      content.append(sourceLink);
    }
    return content;
  }

  function renderEquipmentMap(container, property, radius, features) {
    const origin = property.coordenadas;
    if (!window.L || !origin || !Number.isFinite(origin.lat) || !Number.isFinite(origin.lon)) {
      const unavailable = document.createElement("p");
      unavailable.className = "data-note";
      unavailable.textContent = "El mapa no está disponible para esta ficha.";
      container.replaceWith(unavailable);
      return;
    }

    equipmentMap = window.L.map(container, { scrollWheelZoom: false }).setView([origin.lat, origin.lon], 15);
    window.L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>'
    }).addTo(equipmentMap);

    const bounds = window.L.latLngBounds([[origin.lat, origin.lon]]);
    window.L.circle([origin.lat, origin.lon], {
      radius,
      color: "#53656b",
      weight: 1,
      fillColor: "#53656b",
      fillOpacity: 0.07
    }).addTo(equipmentMap);
    const propertyFeature = { properties: {}, geometry: { coordinates: [origin.lon, origin.lat] } };
    window.L.circleMarker([origin.lat, origin.lon], {
      radius: 8,
      color: "#171b1c",
      weight: 2,
      fillColor: "#f0f0ec",
      fillOpacity: 1
    }).addTo(equipmentMap).bindPopup(popupContent("Ubicación de referencia del inmueble", "Precisión reportada: " + labelCase(property.coordenadas.precision), propertyFeature));

    (features || []).forEach((feature) => {
      const point = feature.geometry?.coordinates;
      if (!Array.isArray(point) || point.length !== 2 || !point.every(Number.isFinite)) return;
      const marker = window.L.circleMarker([point[1], point[0]], {
        radius: 6,
        color: facilityColor(feature.properties?.categoria).stroke,
        weight: 1.5,
        fillColor: facilityColor(feature.properties?.categoria).fill,
        fillOpacity: 0.96
      }).addTo(equipmentMap);
      marker.bindPopup(popupContent(
        text(feature.properties?.nombre, "Nombre no disponible en la fuente"),
        labelCase(feature.properties?.categoria),
        feature,
        origin
      ));
      if (feature.properties?.osm_id) facilityMarkers.set(feature.properties.osm_id, marker);
      bounds.extend([point[1], point[0]]);
    });
    if ((features || []).length) equipmentMap.fitBounds(bounds.pad(0.12), { maxZoom: 16 });
    requestAnimationFrame(() => equipmentMap?.invalidateSize());
  }

  function render(record, index, count, facilityFeatures) {
    if (equipmentMap) {
      equipmentMap.remove();
      equipmentMap = null;
    }
    facilityMarkers = new Map();
    const property = record.inmueble;
    const market = record.mercado;
    const price = market.precio_m2;
    const environment = record.entorno;
    const station = environment.estacion_mas_cercana;
    const article = document.createElement("div");
    const heading = document.createElement("h2");
    heading.textContent = displayId(record.id_inmueble);
    const subtitle = document.createElement("p");
    subtitle.className = "property-subtitle";
    const area = property.area_m2 == null ? "Área no disponible" : `${areaFormatter.format(property.area_m2)} m²`;
    subtitle.textContent = `${labelCase(property.barrio)}, ${municipality(property.municipio)} · ${area}`;

    const priceBlock = document.createElement("div");
    priceBlock.className = "price-block";
    const label = document.createElement("p");
    label.className = "price-label";
    label.textContent = "Mediana del precio anunciado por m²";
    const priceValue = document.createElement("p");
    priceValue.className = "price-value";
    let displayedMedian = price.mediana;
    let displayedComparableCount = price.n;
    priceValue.textContent = money(displayedMedian);
    const range = document.createElement("p");
    range.className = "price-range";
    range.textContent = `Entre ${money(price.minimo)} y ${money(price.maximo)} por m² en los anuncios comparables`;
    priceBlock.append(label, priceValue, range);

    if (record.id_inmueble === "INM-04") {
      const comparableToggle = document.createElement("button");
      comparableToggle.type = "button";
      comparableToggle.className = "comparable-toggle";
      comparableToggle.setAttribute("aria-pressed", "true");
      const updateComparableToggle = () => {
        comparableToggle.textContent = include4375000 ? "Quitar grupo de COP 4.375.000/m² (3)" : "Agregar grupo de COP 4.375.000/m² (3)";
        comparableToggle.setAttribute("aria-pressed", String(include4375000));
        const included = include4375000
          ? market.comparables
          : market.comparables.filter((item) => item.precio_m2 !== 4375000);
        const values = included.map((item) => item.precio_m2).filter(Number.isFinite).sort((a, b) => a - b);
        const middle = Math.floor(values.length / 2);
        displayedMedian = values.length % 2 ? values[middle] : Math.round((values[middle - 1] + values[middle]) / 2);
        displayedComparableCount = values.length;
        priceValue.textContent = money(displayedMedian);
        comparableCountValue.textContent = formatter.format(displayedComparableCount);
      };
      comparableToggle.addEventListener("click", () => {
        include4375000 = !include4375000;
        updateComparableToggle();
      });
      comparableToggle.textContent = "Quitar grupo de COP 4.375.000/m² (3)";
      priceBlock.append(comparableToggle);
    }

    const stats = document.createElement("div");
    stats.className = "stat-grid";
    const comparableCountStat = stat(formatter.format(displayedComparableCount), "Anuncios comparables");
    const comparableCountValue = comparableCountStat.querySelector("b");
    stats.append(
      comparableCountStat,
      stat(labelCase(text(market.confianza.nivel, "No calculada")), "Nivel de confianza"),
      stat(`${formatter.format(environment.radio_busqueda_m)} m`, "Radio de análisis")
    );

    const details = document.createElement("dl");
    details.className = "detail-grid";
    details.append(
      row("Dirección reportada", text(property.direccion)),
      row("Estado reportado", labelCase(property.estado_texto)),
      row("Zona de mercado", labelCase(property.zona)),
      row("Nivel de geocodificación", labelCase(property.coordenadas.precision) === "Cruce" ? "Cruce de vías" : labelCase(property.coordenadas.precision)),
      row("Estación de transporte más cercana", station ? `${station.nombre} (${formatter.format(station.distancia_m)} m)` : "No disponible"),
      row("Tratamiento urbanístico (POT)", record.norma.estado === "pendiente_capa" ? "Pendiente: falta la capa del POT" : labelCase(record.norma.estado))
    );

    const facilitiesTitle = document.createElement("h3");
    facilitiesTitle.className = "subsection-title";
    facilitiesTitle.textContent = "Equipamientos cercanos";
    const facilities = document.createElement("ul");
    facilities.className = "category-list";
    const coordinates = property.coordenadas;
    const nearbyFacilities = coordinates && Number.isFinite(coordinates.lat) && Number.isFinite(coordinates.lon)
      ? (facilityFeatures || []).filter((feature) => {
          const point = feature.geometry?.coordinates;
          return Array.isArray(point) && point.length === 2 &&
            featureDistanceMeters(coordinates.lat, coordinates.lon, point[1], point[0]) <= environment.radio_busqueda_m;
        })
      : [];
    const facilityNote = document.createElement("p");
    facilityNote.className = "data-note";
    facilityNote.textContent = facilityFeatures
      ? `Cada categoría muestra los puntos de la capa preparada dentro de un radio de ${formatter.format(environment.radio_busqueda_m)} m.`
      : "No se pudo cargar el detalle de los equipamientos.";
    Object.entries(environment.equipamientos_en_radio || {}).forEach(([category, amount]) => {
      const item = document.createElement("li");
      const details = document.createElement("details");
      details.className = "facility-category";
      const summary = document.createElement("summary");
      const name = document.createElement("span");
      name.className = "category-name";
      const key = document.createElement("span");
      key.className = "map-key category-key";
      key.setAttribute("aria-hidden", "true");
      key.style.backgroundColor = facilityColor(category).fill;
      key.style.borderColor = facilityColor(category).stroke;
      const label = document.createElement("span");
      label.textContent = labelCase(category);
      name.append(key, label);
      const total = document.createElement("strong");
      total.textContent = formatter.format(amount);
      summary.append(name, total);
      details.append(summary);
      if (facilityFeatures) {
        const entries = nearbyFacilities.filter((feature) => feature.properties?.categoria === category);
        const names = document.createElement("ol");
        names.className = "facility-names";
        entries.forEach((feature) => {
          const entry = document.createElement("li");
          const label = document.createElement("button");
          label.type = "button";
          label.className = "facility-name-button";
          label.textContent = text(feature.properties?.nombre, "Nombre no disponible en la fuente");
          label.addEventListener("click", () => {
            const marker = facilityMarkers.get(feature.properties?.osm_id);
            if (marker) {
              marker.openPopup();
              if (window.matchMedia("(max-width: 700px)").matches) {
                document.getElementById("equipment-map")?.scrollIntoView({ behavior: "smooth", block: "center" });
              }
            }
          });
          entry.append(label);
          names.append(entry);
        });
        if (entries.length === 0) {
          const empty = document.createElement("li");
          empty.textContent = "No hay puntos de esta categoría dentro del radio de análisis.";
          names.append(empty);
        }
        details.append(names);
      }
      item.append(details);
      facilities.append(item);
    });

    const mapSection = document.createElement("section");
    mapSection.className = "map-section";
    const mapHeading = document.createElement("h3");
    mapHeading.className = "map-title";
    mapHeading.textContent = "Mapa de equipamientos cercanos";
    const mapContainer = document.createElement("div");
    mapContainer.id = "equipment-map";
    mapContainer.className = "facility-map";
    mapContainer.setAttribute("role", "region");
    mapContainer.setAttribute("aria-label", "Mapa interactivo del inmueble y los equipamientos cercanos");
    const mapLegend = document.createElement("ul");
    mapLegend.className = "map-legend";
    const propertyKey = document.createElement("span");
    propertyKey.className = "map-key property";
    propertyKey.setAttribute("aria-hidden", "true");
    const propertyLegend = document.createElement("li");
    propertyLegend.append(propertyKey, document.createTextNode("Ubicación de referencia del inmueble"));
    mapLegend.append(propertyLegend);
    Object.keys(environment.equipamientos_en_radio || {}).forEach((category) => {
      const key = document.createElement("span");
      key.className = "map-key category-key";
      key.setAttribute("aria-hidden", "true");
      key.style.backgroundColor = facilityColor(category).fill;
      key.style.borderColor = facilityColor(category).stroke;
      const entry = document.createElement("li");
      entry.append(key, document.createTextNode(labelCase(category)));
      mapLegend.append(entry);
    });
    const mapNote = document.createElement("p");
    mapNote.className = "data-note";
    mapNote.textContent = "Selecciona un punto para ver sus datos y abrir la ruta caminando en Google Maps. La ubicación del inmueble conserva el nivel de geocodificación reportado.";
    mapSection.append(mapHeading, mapContainer, mapLegend, mapNote);

    const status = document.createElement("section");
    status.className = "status";
    const confidenceTitle = document.createElement("h3");
    confidenceTitle.className = "quality-heading";
    confidenceTitle.textContent = "Nivel de confianza:";
    const confidenceList = document.createElement("ul");
    confidenceList.className = "quality-list";
    const confidenceLevel = text(market.confianza.nivel, "no calculada").toLocaleLowerCase("es-CO");
    const confidenceReason = text(market.confianza.motivo, "No hay una explicación disponible.");
    const confidenceEvidence = confidenceReason.split(";")[0].replace(/[.]$/, "");
    const confidenceRules = {
      alta: "Cumple la regla alta (5 o más comparables y coeficiente de variación de hasta 15%).",
      media: "Cumple la regla media (3 o más comparables y coeficiente de variación de hasta 25%, siempre que no aplique la regla alta).",
      baja: "No cumple la regla media (3 o más comparables y coeficiente de variación de hasta 25%)."
    };
    [
      `${labelCase(confidenceLevel)}.`,
      `${confidenceEvidence}.`,
      confidenceRules[confidenceLevel] || "No se puede asignar un nivel sin comparables válidos."
    ].forEach((itemText) => {
      const item = document.createElement("li");
      item.textContent = itemText;
      confidenceList.append(item);
    });
    status.append(confidenceTitle, confidenceList);

    const note = document.createElement("section");
    note.className = "missing-data";
    const missingTitle = document.createElement("h3");
    missingTitle.className = "quality-heading";
    missingTitle.textContent = "Datos faltantes o no disponibles:";
    const missingList = document.createElement("ul");
    missingList.className = "quality-list";
    const missing = list(record.datos_faltantes).map((item) => {
      const field = typeof item === "string" ? item : item.campo || item.dato;
      return missingLabels[field] || labelCase(field);
    }).filter(Boolean);
    (missing.length ? missing : ["No se identificaron datos faltantes."]).forEach((itemText) => {
      const item = document.createElement("li");
      item.textContent = `${itemText}.`;
      missingList.append(item);
    });
    note.append(missingTitle, missingList);

    const links = document.createElement("div");
    links.className = "property-links";
    const fullJson = document.createElement("a");
    fullJson.href = `data/fichas/${record.id_inmueble}.json`;
    fullJson.textContent = "Consultar datos estructurados (JSON)";
    const fullCard = document.createElement("a");
    fullCard.href = `data/cards/${record.id_inmueble}.md`;
    fullCard.textContent = "Consultar ficha detallada (Markdown)";
    links.append(fullJson, fullCard);

    article.append(heading, subtitle, priceBlock, stats, details, facilitiesTitle, facilityNote, facilities, mapSection, status, note, links);
    view.replaceChildren(article);
    renderEquipmentMap(mapContainer, property, environment.radio_busqueda_m, nearbyFacilities);
    picker.querySelectorAll("button").forEach((button, buttonIndex) => {
      button.setAttribute("aria-pressed", String(buttonIndex === index));
    });
    const liveTitle = document.createElement("span");
    liveTitle.className = "eyebrow";
    liveTitle.textContent = `Ficha ${String(index + 1).padStart(2, "0")} de ${String(count).padStart(2, "0")}`;
    view.prepend(liveTitle);
  }

  function featureDistanceMeters(lat1, lon1, lat2, lon2) {
    const radius = 6_371_008.8;
    const radians = (degrees) => degrees * Math.PI / 180;
    const deltaLatitude = radians(lat2 - lat1);
    const deltaLongitude = radians(lon2 - lon1);
    const value = Math.sin(deltaLatitude / 2) ** 2 +
      Math.cos(radians(lat1)) * Math.cos(radians(lat2)) * Math.sin(deltaLongitude / 2) ** 2;
    return 2 * radius * Math.asin(Math.sqrt(Math.min(1, value)));
  }

  async function start() {
    const ids = Array.from({ length: 11 }, (_, index) => `INM-${String(index + 1).padStart(2, "0")}`);
    const [records, facilityLayer] = await Promise.all([Promise.all(ids.map(async (id) => {
      const response = await fetch(`data/fichas/${id}.json`);
      if (!response.ok) throw new Error(`No se pudo cargar ${id}`);
      return response.json();
    })), fetch("output/prepared/geo/equipamientos_limpios.geojson").then((response) => {
      if (!response.ok) throw new Error("No se pudo cargar la capa de equipamientos");
      return response.json();
    }).catch((error) => {
      console.error(error);
      return null;
    })]);
    const facilityFeatures = Array.isArray(facilityLayer?.features) ? facilityLayer.features : null;

    records.forEach((record, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "property-choice";
      button.setAttribute("aria-pressed", "false");
      const id = document.createElement("span");
      id.textContent = displayId(record.id_inmueble);
      const arrow = document.createElement("small");
      arrow.textContent = "↗";
      button.append(id, arrow);
      button.addEventListener("click", () => render(record, index, records.length, facilityFeatures));
      picker.append(button);
    });
    render(records[0], 0, records.length, facilityFeatures);
  }

  start().catch((error) => {
    view.replaceChildren();
    const message = document.createElement("p");
    message.className = "status-error";
    message.textContent = "No se pudieron cargar las fichas. Recarga la página o inténtalo más tarde.";
    view.append(message);
    console.error(error);
  });
})();
