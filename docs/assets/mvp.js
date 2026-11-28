(() => {
  const picker = document.getElementById("property-picker");
  const view = document.getElementById("property-view");
  const formatter = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
  const areaFormatter = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });
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

  function render(record, index, count, facilityFeatures) {
    const property = record.inmueble;
    const market = record.mercado;
    const price = market.precio_m2;
    const environment = record.entorno;
    const station = environment.estacion_mas_cercana;
    const article = document.createElement("div");
    const heading = document.createElement("h2");
    heading.textContent = record.id_inmueble;
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
    priceValue.textContent = money(price.mediana);
    const range = document.createElement("p");
    range.className = "price-range";
    range.textContent = `Rango: ${money(price.minimo)} a ${money(price.maximo)}`;
    priceBlock.append(label, priceValue, range);

    const stats = document.createElement("div");
    stats.className = "stat-grid";
    stats.append(
      stat(formatter.format(price.n), "Anuncios comparables"),
      stat(labelCase(text(market.confianza.nivel, "No calculada")), "Nivel de confianza"),
      stat(`${formatter.format(environment.radio_busqueda_m)} m`, "Radio de análisis")
    );

    const details = document.createElement("dl");
    details.className = "detail-grid";
    details.append(
      row("Dirección reportada", text(property.direccion)),
      row("Estado reportado", labelCase(property.estado_texto)),
      row("Zona de mercado", labelCase(property.zona)),
      row("Precisión de coordenadas", labelCase(property.coordenadas.precision)),
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
      name.textContent = labelCase(category);
      const total = document.createElement("strong");
      total.textContent = formatter.format(amount);
      summary.append(name, total);
      details.append(summary);
      if (facilityFeatures) {
        const entries = nearbyFacilities.filter((feature) => feature.properties?.categoria === category);
        const names = document.createElement("ul");
        names.className = "facility-names";
        entries.forEach((feature) => {
          const entry = document.createElement("li");
          const label = document.createElement("span");
          label.textContent = text(feature.properties?.nombre, "Nombre no disponible en la fuente");
          entry.append(label);
          if (feature.properties?.osm_id) {
            const identifier = document.createElement("code");
            identifier.textContent = feature.properties.osm_id;
            entry.append(identifier);
          }
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

    const status = document.createElement("p");
    status.className = "status";
    status.textContent = `Nivel de confianza: ${labelCase(text(market.confianza.nivel, "no calculado"))}. ${text(market.confianza.motivo, "No hay una explicación disponible.")}`;

    const note = document.createElement("p");
    note.className = "data-note";
    const missing = list(record.datos_faltantes).map((item) => {
      const field = typeof item === "string" ? item : item.campo || item.dato;
      return missingLabels[field] || labelCase(field);
    }).filter(Boolean);
    note.textContent = missing.length ? `Datos faltantes o no disponibles: ${missing.join(", ")}.` : "No se identificaron datos faltantes para este inmueble.";

    const links = document.createElement("div");
    links.className = "property-links";
    const fullJson = document.createElement("a");
    fullJson.href = `data/fichas/${record.id_inmueble}.json`;
    fullJson.textContent = "Consultar datos estructurados (JSON)";
    const fullCard = document.createElement("a");
    fullCard.href = `data/cards/${record.id_inmueble}.md`;
    fullCard.textContent = "Consultar ficha detallada (Markdown)";
    links.append(fullJson, fullCard);

    article.append(heading, subtitle, priceBlock, stats, details, facilitiesTitle, facilityNote, facilities, status, note, links);
    view.replaceChildren(article);
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
      id.textContent = record.id_inmueble;
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
