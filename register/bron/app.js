/* CSIR-keten: classificeren, bepalen, uitwerken. Rekent volledig in de browser.
 *
 * De pagina bevat geen eigen kopie van de richtlijn: alle eisteksten, maatregelen, drempels en
 * keuzelijsten komen uit window.__BRON__ (gebouwd uit csir.json). Een test blokkeert als hier toch
 * een code of eistekst in de code zelf terechtkomt.
 *
 * Het object `reken` hieronder is de spiegel van register/reken.py: dezelfde functienamen, dezelfde
 * regels, in dezelfde volgorde. De browsertests vergelijken de uitkomst op het scherm met die van
 * het Python-bestand, dus de twee kunnen niet stil uit elkaar lopen. Daarom staan hier ook
 * Python-achtige namen met liggende streepjes; dat is bewust, geen slordigheid.
 */
(function () {
  'use strict';

  var BRON = window.__BRON__;
  var OPSLAG = 'csir-dossier';
  var TABEL = BRON.functiebox_niveau;
  var LEEG_STATUS = '(leeg)';

  /* ---------------------------------------------------------------- reken */

  var reken = {};

  reken.rond_half_omhoog = function (getal) {
    // Excel ROUND: 2,5 wordt 3. Math.round doet dat voor positieve getallen ook, maar niet voor
    // negatieve; floor(x + 0.5) is aan beide kanten hetzelfde als in Python.
    return Math.floor(getal + 0.5);
  };

  reken.procent = function (deel) {
    // 1 van de 8 is 12,5 procent en dat wordt 13, aan beide kanten. Zie reken.py.
    return reken.rond_half_omhoog(deel * 100) + '%';
  };

  reken.niveau_van_functiebox = function (functiebox, tabel) {
    if (Object.prototype.hasOwnProperty.call(tabel, functiebox)) {
      return { niveau: tabel[functiebox], voorlopig: false };
    }
    return { niveau: 1, voorlopig: true };
  };

  reken.effectief_niveau = function (instellingen, tabel) {
    var eigen = reken.niveau_van_functiebox((instellingen && instellingen.functiebox) || '', tabel);
    var keten = 0;
    var k = (instellingen && instellingen.keten) || {};
    if (k.actief) {
      (k.objecten || []).forEach(function (object) {
        var box = (object && object.functiebox) || '';
        if (Object.prototype.hasOwnProperty.call(tabel, box)) keten = Math.max(keten, tabel[box]);
      });
    }
    return {
      eigen: eigen.niveau,
      keten: keten,
      effectief: Math.max(eigen.niveau, keten),
      voorlopig: eigen.voorlopig
    };
  };

  reken.klassificeer = function (scores, ernst) {
    var perScore = {};
    ernst.forEach(function (rij) { perScore[rij.score] = rij; });
    var sleutels = Object.keys(scores);
    var waarden = sleutels.map(function (s) { return scores[s]; });
    if (!waarden.length || waarden.some(function (w) { return w === null || w === undefined; })) {
      return { compleet: false };
    }
    var som = waarden.reduce(function (a, b) { return a + b; }, 0);
    var gemiddelde = reken.rond_half_omhoog(som / waarden.length);
    var hoogste = Math.max.apply(null, waarden);
    return {
      compleet: true,
      som: som,
      gemiddelde: gemiddelde,
      hoogste: hoogste,
      gemiddelde_label: perScore[gemiddelde].label,
      gemiddelde_functiebox: perScore[gemiddelde].functiebox,
      gemiddelde_niveau: perScore[gemiddelde].niveau,
      hoogste_label: perScore[hoogste].label,
      hoogste_functiebox: perScore[hoogste].functiebox,
      hoogste_niveau: perScore[hoogste].niveau
    };
  };

  reken.ouder = function (paragraaf) {
    if ((paragraaf.match(/\./g) || []).length >= 2) {
      var eerste = paragraaf.indexOf('.');
      var tweede = paragraaf.indexOf('.', eerste + 1);
      return paragraaf.slice(0, tweede);
    }
    return paragraaf;
  };

  reken.geldt = function (maatregel, niveau) {
    return maatregel.niveaus.indexOf(niveau) !== -1;
  };

  reken.aanroepende_controls = function (paragraaf, controls) {
    var boven = reken.ouder(paragraaf);
    return controls.filter(function (c) {
      return c.aangeroepen.indexOf(paragraaf) !== -1 || c.aangeroepen.indexOf(boven) !== -1;
    });
  };

  function vanToepassing(dossier, soort, sleutel) {
    var regel = (dossier[soort] || {})[sleutel];
    return (regel && regel.vt) || '';
  }

  function statusVan(dossier, soort, sleutel) {
    var regel = (dossier[soort] || {})[sleutel];
    return (regel && regel.status) || '';
  }

  reken.scope = function (maatregel, niveau, controls, dossier) {
    if (!reken.geldt(maatregel, niveau)) return 'Niet op dit niveau';
    var betrokken = AANROEP[maatregel.paragraaf] ||
      reken.aanroepende_controls(maatregel.paragraaf, controls);
    var ja = 0;
    var leeg = 0;
    betrokken.forEach(function (c) {
      var vt = vanToepassing(dossier, 'controls', c.id);
      if (vt === 'Ja') ja += 1;
      if (!vt) leeg += 1;
    });
    if (ja > 0) return 'In scope';
    if (betrokken.length && leeg === 0) return 'Buiten scope';
    return 'Nog te bepalen';
  };

  var STATUS_TELLER = {
    'Nog te doen': 'todo',
    'In uitvoering': 'bezig',
    'Geïmplementeerd': 'klaar',
    'Explain (afwijking)': 'explain',
    'N.v.t.': 'nvt'
  };

  function leegTellingen() {
    return { todo: 0, bezig: 0, klaar: 0, explain: 0, nvt: 0 };
  }

  function rij(vt, tellingen) {
    var noemer = vt - tellingen.nvt;
    var uit = { vt: vt };
    Object.keys(tellingen).forEach(function (s) { uit[s] = tellingen[s]; });
    uit.pct_impl = noemer <= 0 ? 0 : tellingen.klaar / noemer;
    uit.pct_afgeh = noemer <= 0 ? 0 : (tellingen.klaar + tellingen.explain) / noemer;
    return uit;
  }

  reken.dashboard = function (bron, dossier) {
    var niveau = reken.effectief_niveau(dossier.instellingen || {}, bron.functiebox_niveau).effectief;
    var controls = bron.controls;
    var uit = { niveau: niveau };
    var somVt = 0;
    var somTellingen = leegTellingen();

    ['VSP', 'VSE'].forEach(function (blad) {
      var tellingen = leegTellingen();
      var vt = 0;
      controls.forEach(function (control) {
        if (control.blad !== blad) return;
        if (vanToepassing(dossier, 'controls', control.id) !== 'Ja') return;
        vt += 1;
        var sleutel = STATUS_TELLER[statusVan(dossier, 'controls', control.id)];
        if (sleutel) tellingen[sleutel] += 1;
      });
      uit[blad.toLowerCase()] = rij(vt, tellingen);
      somVt += vt;
      Object.keys(somTellingen).forEach(function (s) { somTellingen[s] += tellingen[s]; });
    });

    var opNiveau = bron.maatregelen.filter(function (m) { return reken.geldt(m, niveau); });
    var tellingen = leegTellingen();
    opNiveau.forEach(function (maatregel) {
      var sleutel = STATUS_TELLER[statusVan(dossier, 'maatregelen', maatregel.code)];
      if (sleutel) tellingen[sleutel] += 1;
    });
    uit.maatregelen = rij(opNiveau.length, tellingen);
    somVt += opNiveau.length;
    Object.keys(somTellingen).forEach(function (s) { somTellingen[s] += tellingen[s]; });
    uit.totaal = rij(somVt, somTellingen);

    var telVt = { ja: 0, nee: 0, nvt: 0, leeg: 0 };
    controls.forEach(function (c) {
      var vt = vanToepassing(dossier, 'controls', c.id);
      if (vt === 'Ja') telVt.ja += 1;
      else if (vt === 'Nee') telVt.nee += 1;
      else if (vt) telVt.nvt += 1;
      else telVt.leeg += 1;
    });
    uit.controls = telVt;

    var telScope = { in: 0, buiten: 0, nog: 0 };
    bron.maatregelen.forEach(function (m) {
      var s = reken.scope(m, niveau, controls, dossier);
      if (s === 'In scope') telScope['in'] += 1;
      else if (s === 'Buiten scope') telScope.buiten += 1;
      else if (s === 'Nog te bepalen') telScope.nog += 1;
    });
    uit.scope = telScope;

    var perParagraaf = {};
    bron.paragrafen.forEach(function (paragraaf) {
      var rijen = bron.maatregelen.filter(function (m) {
        return m.paragraaf === paragraaf.id && reken.geldt(m, niveau);
      });
      var klaar = rijen.filter(function (m) {
        return statusVan(dossier, 'maatregelen', m.code) === 'Geïmplementeerd';
      }).length;
      perParagraaf[paragraaf.id] = {
        op_niveau: rijen.length,
        geimpl: klaar,
        pct: rijen.length ? klaar / rijen.length : null
      };
    });
    uit.paragraaf = perParagraaf;
    return uit;
  };

  reken.nieuw_dossier = function (bron) {
    var scores = {};
    var onderbouwing = {};
    bron.classificatie.criteria.forEach(function (c) {
      scores[c.id] = null;
      onderbouwing[c.id] = '';
    });
    var controls = {};
    bron.controls.forEach(function (c) {
      controls[c.id] = { vt: bron.keuzes.van_toepassing[0], status: '', bewijs: '',
        verantwoordelijke: '', opmerking: '' };
    });
    return {
      formaat: 'csir-dossier',
      versie: 1,
      bron_versie: bron.versie,
      bron_sha256: bron.vingerafdruk,
      bijgewerkt: '',
      object: { naam: '', organisatie: '', proces: '', locatie: '', hoofdtaak: '', situatie: '',
        ingevuld_door: '', team: '', datum: '' },
      classificatie: { scores: scores, onderbouwing: onderbouwing, opmerkingen: '' },
      instellingen: {
        functiebox: '', functiebox_bron: '',
        keten: { actief: false,
          objecten: [{ naam: '', functiebox: '' }, { naam: '', functiebox: '' },
            { naam: '', functiebox: '' }],
          bevestigd_door: '', datum: '' }
      },
      controls: controls,
      maatregelen: {},
      bijlagen: {}
    };
  };

  /* --------------------------------------------------------------- opzet */

  // De koppeling paragraaf naar aanroepende controls verandert nooit; een keer uitrekenen scheelt
  // 268 keer zoeken bij elke toetsaanslag.
  var AANROEP = {};
  BRON.paragrafen.forEach(function (paragraaf) {
    AANROEP[paragraaf.id] = reken.aanroepende_controls(paragraaf.id, BRON.controls);
  });

  var PARAGRAAF = {};
  BRON.paragrafen.forEach(function (p) { PARAGRAAF[p.id] = p; });

  var dossier = laadUitOpslag() || reken.nieuw_dossier(BRON);
  var melding = '';

  function el(id) { return document.getElementById(id); }

  function maak(tag, tekst, klasse) {
    var node = document.createElement(tag);
    if (tekst !== undefined && tekst !== null) node.textContent = String(tekst);
    if (klasse) node.className = klasse;
    return node;
  }

  function opties(select, waarden, leegLabel) {
    if (leegLabel !== null && leegLabel !== undefined) {
      var leeg = maak('option', leegLabel);
      leeg.value = '';
      select.appendChild(leeg);
    }
    waarden.forEach(function (waarde) {
      var optie = maak('option', waarde);
      optie.value = waarde;
      select.appendChild(optie);
    });
  }

  function procent(deel) {
    return reken.procent(deel);
  }

  function eisTekst(control) {
    if (!control.sjabloon) return control.eis;
    var niveau = reken.effectief_niveau(dossier.instellingen, TABEL).effectief;
    return control.eis
      .replace('{object}', dossier.object.naam || '(nog geen object ingevuld)')
      .replace('{niveau}', String(niveau));
  }

  function regelVan(soort, sleutel) {
    if (!dossier[soort][sleutel]) {
      dossier[soort][sleutel] = { vt: '', status: '', bewijs: '', verantwoordelijke: '', opmerking: '' };
    }
    return dossier[soort][sleutel];
  }

  /* -------------------------------------------------------------- opslag */

  function laadUitOpslag() {
    try {
      var ruw = window.localStorage.getItem(OPSLAG);
      if (!ruw) return null;
      var gelezen = JSON.parse(ruw);
      return gelezen && gelezen.formaat === 'csir-dossier' ? gelezen : null;
    } catch (fout) {
      return null;
    }
  }

  function bewaar() {
    dossier.bijgewerkt = new Date().toISOString().slice(0, 19);
    try {
      window.localStorage.setItem(OPSLAG, JSON.stringify(dossier));
    } catch (fout) {
      melding = 'Opslaan in deze browser lukt niet; sla je dossier op als bestand.';
    }
  }

  function slug(tekst) {
    var uit = (tekst || 'object').toLowerCase().replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '').slice(0, 40);
    return uit || 'object';
  }

  function opslaanAlsBestand() {
    var naam = 'csir-dossier-' + slug(dossier.object.naam) + '-' +
      new Date().toISOString().slice(0, 10) + '.json';
    var blob = new Blob([JSON.stringify(dossier, null, 1)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = naam;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(function () { URL.revokeObjectURL(url); }, 0);
  }

  function ladenUitBestand(bestand) {
    var lezer = new FileReader();
    lezer.onload = function () {
      var gelezen;
      try {
        gelezen = JSON.parse(String(lezer.result));
      } catch (fout) {
        melding = 'Dit is geen dossier: het bestand is geen geldige JSON.';
        tekenAlles();
        return;
      }
      if (!gelezen || gelezen.formaat !== 'csir-dossier' || gelezen.versie !== 1) {
        melding = 'Dit is geen dossier van deze tool (formaat of versie klopt niet); ' +
          'er is niets overschreven.';
        tekenAlles();
        return;
      }
      var onbekend = 0;
      ['controls', 'maatregelen', 'bijlagen'].forEach(function (soort) {
        var bekend = {};
        (soort === 'controls' ? BRON.controls : soort === 'maatregelen' ? BRON.maatregelen
          : BRON.bijlagen).forEach(function (regel) {
          bekend[regel.id || regel.code] = true;
        });
        Object.keys(gelezen[soort] || {}).forEach(function (sleutel) {
          if (!bekend[sleutel]) {
            delete gelezen[soort][sleutel];
            onbekend += 1;
          }
        });
      });
      dossier = gelezen;
      melding = '';
      if (gelezen.bron_sha256 && gelezen.bron_sha256 !== BRON.vingerafdruk) {
        melding = 'Let op: dit dossier is gemaakt met bronversie ' +
          (gelezen.bron_versie || 'onbekend') + '; deze pagina gebruikt ' + BRON.versie +
          '. Controleer de tellers.';
      }
      if (onbekend) {
        melding += (melding ? ' ' : '') + onbekend +
          ' regel(s) uit het dossier kende deze pagina niet en zijn overgeslagen.';
      }
      bewaar();
      tekenAlles();
    };
    lezer.readAsText(bestand);
  }

  /* ------------------------------------------------------------- tabbladen */

  var SCHERMEN = ['classificatie', 'instellingen', 'dashboard', 'vsp', 'vse', 'maatregelen',
    'bijlagen', 'uitdraai'];

  function toon(naam) {
    SCHERMEN.forEach(function (s) {
      var scherm = el('scherm-' + s);
      var tab = el('tab-' + s);
      var actief = s === naam;
      scherm.hidden = !actief;
      tab.setAttribute('aria-selected', actief ? 'true' : 'false');
    });
    if (naam === 'uitdraai') tekenUitdraai();
  }

  /* --------------------------------------------------------- classificatie */

  function bouwClassificatie() {
    var houder = el('criteria');
    BRON.classificatie.criteria.forEach(function (criterium) {
      var blok = maak('div', null, 'kaart');
      blok.appendChild(maak('h3', criterium.titel));
      blok.appendChild(maak('p', criterium.uitleg, 'klein'));

      var label = maak('label', 'Ernst');
      var select = maak('select');
      select.setAttribute('data-criterium', criterium.id);
      var leeg = maak('option', 'nog niet gescoord');
      leeg.value = '';
      select.appendChild(leeg);
      BRON.classificatie.ernst.forEach(function (ernst) {
        var optie = maak('option', ernst.score + ' · ' + ernst.label + ' · ' +
          criterium.drempels[String(ernst.score)].replace(/\s+/g, ' '));
        optie.value = String(ernst.score);
        select.appendChild(optie);
      });
      label.appendChild(select);
      blok.appendChild(label);

      var onderbouwing = maak('label', 'Onderbouwing', 'breed');
      var veld = maak('textarea');
      veld.rows = 2;
      veld.setAttribute('data-onderbouwing', criterium.id);
      onderbouwing.appendChild(veld);
      blok.appendChild(onderbouwing);

      houder.appendChild(blok);
    });

    houder.addEventListener('change', function (gebeurtenis) {
      var doel = gebeurtenis.target;
      if (doel.hasAttribute('data-criterium')) {
        var waarde = doel.value;
        dossier.classificatie.scores[doel.getAttribute('data-criterium')] =
          waarde === '' ? null : parseInt(waarde, 10);
        bewaar();
        tekenClassificatie();
      }
    });
    houder.addEventListener('input', function (gebeurtenis) {
      var doel = gebeurtenis.target;
      if (doel.hasAttribute('data-onderbouwing')) {
        dossier.classificatie.onderbouwing[doel.getAttribute('data-onderbouwing')] = doel.value;
        bewaar();
      }
    });
  }

  function tekenClassificatie() {
    BRON.classificatie.criteria.forEach(function (criterium) {
      var select = document.querySelector('[data-criterium="' + criterium.id + '"]');
      var score = dossier.classificatie.scores[criterium.id];
      select.value = score === null || score === undefined ? '' : String(score);
      document.querySelector('[data-onderbouwing="' + criterium.id + '"]').value =
        dossier.classificatie.onderbouwing[criterium.id] || '';
    });
    el('klas-opmerkingen').value = dossier.classificatie.opmerkingen || '';

    var uitkomst = reken.klassificeer(dossier.classificatie.scores, BRON.classificatie.ernst);
    var velden = ['klas-som', 'klas-gemiddelde', 'klas-functiebox', 'klas-niveau', 'klas-hoogste',
      'klas-hoogste-functiebox', 'klas-hoogste-niveau'];
    if (!uitkomst.compleet) {
      velden.forEach(function (id) { el(id).textContent = 'nog niet compleet'; });
      el('knop-classificatie-overnemen').disabled = true;
    } else {
      el('klas-som').textContent = String(uitkomst.som);
      el('klas-gemiddelde').textContent = uitkomst.gemiddelde + ' · ' + uitkomst.gemiddelde_label;
      el('klas-functiebox').textContent = uitkomst.gemiddelde_functiebox;
      el('klas-niveau').textContent = String(uitkomst.gemiddelde_niveau);
      el('klas-hoogste').textContent = uitkomst.hoogste + ' · ' + uitkomst.hoogste_label;
      el('klas-hoogste-functiebox').textContent = uitkomst.hoogste_functiebox;
      el('klas-hoogste-niveau').textContent = String(uitkomst.hoogste_niveau);
      el('knop-classificatie-overnemen').disabled = false;
    }
  }

  /* ---------------------------------------------------------- instellingen */

  function bouwInstellingen() {
    opties(el('obj-functiebox'), BRON.keuzes.functiebox, 'nog niet gekozen');
    opties(el('obj-hoofdtaak'), BRON.classificatie.hoofdtaken, 'nog niet gekozen');

    var lijf = el('keten-rijen');
    for (var i = 0; i < 3; i += 1) {
      var tr = maak('tr');
      var tdNaam = maak('td');
      var naam = maak('input');
      naam.type = 'text';
      naam.setAttribute('data-keten-naam', String(i + 1));
      tdNaam.appendChild(naam);
      var tdBox = maak('td');
      var box = maak('select');
      box.setAttribute('data-keten-fb', String(i + 1));
      opties(box, BRON.keuzes.functiebox, '—');
      tdBox.appendChild(box);
      var tdNiveau = maak('td', '—');
      tdNiveau.setAttribute('data-keten-niveau', String(i + 1));
      tr.appendChild(tdNaam);
      tr.appendChild(tdBox);
      tr.appendChild(tdNiveau);
      lijf.appendChild(tr);
    }

    var tabel = el('tabel-functiebox-rijen');
    BRON.classificatie.ernst.forEach(function (ernst) {
      var tr = maak('tr');
      tr.appendChild(maak('td', ernst.functiebox));
      tr.appendChild(maak('td', String(ernst.niveau)));
      lijf = null;
      tabel.appendChild(tr);
    });
  }

  function tekenInstellingen() {
    el('obj-functiebox').value = dossier.instellingen.functiebox || '';
    el('keten-actief').value = dossier.instellingen.keten.actief ? 'ja' : 'nee';
    el('keten-bevestigd').value = dossier.instellingen.keten.bevestigd_door || '';
    el('keten-datum').value = dossier.instellingen.keten.datum || '';
    el('obj-naam-2').value = dossier.object.naam || '';

    for (var i = 0; i < 3; i += 1) {
      var object = dossier.instellingen.keten.objecten[i] || { naam: '', functiebox: '' };
      document.querySelector('[data-keten-naam="' + (i + 1) + '"]').value = object.naam || '';
      document.querySelector('[data-keten-fb="' + (i + 1) + '"]').value = object.functiebox || '';
      var niveau = reken.niveau_van_functiebox(object.functiebox || '', TABEL);
      document.querySelector('[data-keten-niveau="' + (i + 1) + '"]').textContent =
        object.functiebox ? String(niveau.niveau) : '—';
    }

    var uitkomst = reken.effectief_niveau(dossier.instellingen, TABEL);
    el('niveau-eigen').textContent = String(uitkomst.eigen);
    el('niveau-keten').textContent = String(uitkomst.keten);
    el('niveau-effectief').textContent = String(uitkomst.effectief);
    el('waarschuwing-functiebox').hidden = !uitkomst.voorlopig;
    el('waarschuwing-dashboard').hidden = !uitkomst.voorlopig;

    var herkomst = dossier.instellingen.functiebox_bron;
    el('functiebox-herkomst').textContent = !dossier.instellingen.functiebox ? '' :
      herkomst === 'classificatie'
        ? 'Overgenomen uit de classificatie op het eerste tabblad.'
        : 'Handmatig gekozen. Doe de classificatie als je de onderbouwing nog moet vastleggen.';
  }

  /* ------------------------------------------------------------- controls */

  var CONTROL_KOPPEN = ['Nr', 'BIO-bron', 'Control-eis', 'Aangeroepen §2', 'Bijlagen',
    'Van toepassing', 'Status', 'Invulling / bewijs', 'Verantwoordelijke', 'Opmerking'];

  function bouwControls(blad) {
    var tabel = el('tabel-' + blad.toLowerCase());
    var kop = maak('thead');
    var koprij = maak('tr');
    CONTROL_KOPPEN.forEach(function (naam) {
      var th = maak('th', naam);
      th.setAttribute('scope', 'col');
      koprij.appendChild(th);
    });
    kop.appendChild(koprij);
    tabel.appendChild(kop);

    var lijf = maak('tbody');
    BRON.controls.forEach(function (control) {
      if (control.blad !== blad) return;
      var tr = maak('tr');
      tr.setAttribute('data-control', control.id);
      tr.appendChild(maak('td', String(control.nr)));
      tr.appendChild(maak('td', control.bio_bron));
      var eis = maak('td', '', 'tekst');
      eis.setAttribute('data-eis', control.id);
      if (control.kort) eis.title = control.kort;
      tr.appendChild(eis);
      tr.appendChild(maak('td', control.aangeroepen.join(', ') || '—'));
      tr.appendChild(maak('td', control.bijlagen.join(', ') || '—'));

      var tdVt = maak('td');
      var vt = maak('select', null, 'vt');
      opties(vt, BRON.keuzes.van_toepassing, 'nog niet bepaald');
      tdVt.appendChild(vt);
      tr.appendChild(tdVt);

      var tdStatus = maak('td');
      var status = maak('select', null, 'status');
      opties(status, BRON.keuzes.status, 'nog geen status');
      tdStatus.appendChild(status);
      tr.appendChild(tdStatus);

      ['bewijs', 'verantwoordelijke', 'opmerking'].forEach(function (veld) {
        var td = maak('td');
        var invoer = maak('input', null, veld);
        invoer.type = 'text';
        td.appendChild(invoer);
        tr.appendChild(td);
      });
      lijf.appendChild(tr);
    });
    tabel.appendChild(lijf);

    tabel.addEventListener('change', function (gebeurtenis) {
      onControlWijziging(gebeurtenis.target);
    });
    tabel.addEventListener('input', function (gebeurtenis) {
      if (gebeurtenis.target.tagName === 'INPUT') onControlWijziging(gebeurtenis.target);
    });
  }

  function onControlWijziging(doel) {
    var tr = doel.closest ? doel.closest('tr[data-control]') : null;
    if (!tr) return;
    var regel = regelVan('controls', tr.getAttribute('data-control'));
    if (doel.classList.contains('vt')) regel.vt = doel.value;
    else if (doel.classList.contains('status')) regel.status = doel.value;
    else if (doel.classList.contains('bewijs')) regel.bewijs = doel.value;
    else if (doel.classList.contains('verantwoordelijke')) regel.verantwoordelijke = doel.value;
    else if (doel.classList.contains('opmerking')) regel.opmerking = doel.value;
    else return;
    bewaar();
    if (doel.classList.contains('vt') || doel.classList.contains('status')) {
      tekenMaatregelen();
      tekenDashboard();
    }
    tekenStatusregel();
  }

  function tekenControls(blad) {
    var zoek = el('zoek-' + blad.toLowerCase()).value.trim().toLowerCase();
    var zichtbaar = 0;
    var totaal = 0;
    var lijf = el('tabel-' + blad.toLowerCase()).querySelector('tbody');
    BRON.controls.forEach(function (control) {
      if (control.blad !== blad) return;
      totaal += 1;
      var tr = lijf.querySelector('[data-control="' + control.id + '"]');
      var regel = regelVan('controls', control.id);
      var tekst = eisTekst(control);
      tr.querySelector('[data-eis]').textContent = tekst;
      tr.querySelector('.vt').value = regel.vt || '';
      tr.querySelector('.status').value = regel.status || '';
      tr.querySelector('.bewijs').value = regel.bewijs || '';
      tr.querySelector('.verantwoordelijke').value = regel.verantwoordelijke || '';
      tr.querySelector('.opmerking').value = regel.opmerking || '';

      var past = !zoek || (tekst + ' ' + control.bio_bron + ' ' + control.nr + ' ' + control.kort)
        .toLowerCase().indexOf(zoek) !== -1;
      tr.hidden = !past;
      if (past) zichtbaar += 1;
    });
    el('teller-' + blad.toLowerCase()).textContent = zichtbaar + ' van ' + totaal + ' zichtbaar';
  }

  /* ---------------------------------------------------------- maatregelen */

  var MAATREGEL_KOPPEN = ['Code', 'Groep', 'Maatregel', 'Niveaus', 'Geldt', 'Scope', 'Status',
    'Invulling / bewijs', 'Verantwoordelijke', 'Opmerking'];

  function handreikingBlok(paragraaf) {
    var gegevens = BRON.handreiking[paragraaf] || { handleidingen: [], reden: '', barrieres: [] };
    var blok = maak('details');
    blok.setAttribute('data-handreiking', paragraaf);
    var lijst = gegevens.handleidingen || [];
    blok.appendChild(maak('summary', lijst.length
      ? 'Handleidingen uit de kennisbank (' + lijst.length + ')'
      : 'Nog geen handleiding in de kennisbank'));
    if (lijst.length) {
      var ul = maak('ul');
      lijst.forEach(function (handleiding) {
        var li = maak('li');
        var link = maak('a', handleiding.titel);
        link.href = handleiding.url;
        link.rel = 'noopener';
        li.appendChild(link);
        li.appendChild(maak('span', ' · ' + handleiding.rol, 'rol-label'));
        ul.appendChild(li);
      });
      blok.appendChild(ul);
    } else {
      var uitleg = maak('p', gegevens.reden + ' Weet jij hoe dit werkt? Schrijf mee: ', 'klein');
      var link2 = maak('a', 'stel een handleiding voor in de kennisbank');
      link2.href = 'https://github.com/security-commons-nl/kennisbank/issues/new/choose';
      link2.rel = 'noopener';
      uitleg.appendChild(link2);
      blok.appendChild(uitleg);
    }
    return blok;
  }

  function bouwMaatregelen() {
    opties(el('filter-paragraaf'), BRON.paragrafen.map(function (p) { return p.id; }), 'alle');
    Array.prototype.forEach.call(el('filter-paragraaf').options, function (optie) {
      if (optie.value && PARAGRAAF[optie.value]) {
        optie.textContent = optie.value + ' · ' + PARAGRAAF[optie.value].thema;
      }
    });

    var tabel = el('tabel-maatregelen');
    var kop = maak('thead');
    var koprij = maak('tr');
    MAATREGEL_KOPPEN.forEach(function (naam) {
      var th = maak('th', naam);
      th.setAttribute('scope', 'col');
      koprij.appendChild(th);
    });
    kop.appendChild(koprij);
    tabel.appendChild(kop);

    var lijf = maak('tbody');
    var huidige = null;
    BRON.maatregelen.forEach(function (maatregel) {
      if (maatregel.paragraaf !== huidige) {
        huidige = maatregel.paragraaf;
        var koprijPar = maak('tr', null, 'paragraaf');
        koprijPar.setAttribute('data-paragraaf', huidige);
        var td = maak('td');
        td.colSpan = MAATREGEL_KOPPEN.length;
        td.appendChild(maak('span', huidige + '  '));
        td.appendChild(maak('span', PARAGRAAF[huidige].thema, 'thema'));
        td.appendChild(maak('span', '  · ', 'thema'));
        var telling = maak('span', '', 'thema');
        telling.setAttribute('data-partelling', huidige);
        td.appendChild(telling);
        td.appendChild(handreikingBlok(huidige));
        koprijPar.appendChild(td);
        lijf.appendChild(koprijPar);
      }
      var tr = maak('tr');
      tr.setAttribute('data-maatregel', maatregel.code);
      tr.appendChild(maak('td', maatregel.code));
      tr.appendChild(maak('td', maatregel.groep));
      tr.appendChild(maak('td', maatregel.tekst, 'tekst'));
      var niveaus = maak('td', '');
      niveaus.setAttribute('data-niveaus', maatregel.code);
      tr.appendChild(niveaus);
      var geldt = maak('td', '', 'geldt');
      tr.appendChild(geldt);
      var scope = maak('td', '', 'scope');
      tr.appendChild(scope);

      var tdStatus = maak('td');
      var status = maak('select', null, 'status');
      opties(status, BRON.keuzes.status, 'nog geen status');
      tdStatus.appendChild(status);
      tr.appendChild(tdStatus);

      ['bewijs', 'verantwoordelijke', 'opmerking'].forEach(function (veld) {
        var td = maak('td');
        var invoer = maak('input', null, veld);
        invoer.type = 'text';
        td.appendChild(invoer);
        tr.appendChild(td);
      });
      lijf.appendChild(tr);
    });
    tabel.appendChild(lijf);

    tabel.addEventListener('change', function (g) { onMaatregelWijziging(g.target); });
    tabel.addEventListener('input', function (g) {
      if (g.target.tagName === 'INPUT') onMaatregelWijziging(g.target);
    });
  }

  function onMaatregelWijziging(doel) {
    var tr = doel.closest ? doel.closest('tr[data-maatregel]') : null;
    if (!tr) return;
    var regel = regelVan('maatregelen', tr.getAttribute('data-maatregel'));
    if (doel.classList.contains('status')) regel.status = doel.value;
    else if (doel.classList.contains('bewijs')) regel.bewijs = doel.value;
    else if (doel.classList.contains('verantwoordelijke')) regel.verantwoordelijke = doel.value;
    else if (doel.classList.contains('opmerking')) regel.opmerking = doel.value;
    else return;
    bewaar();
    if (doel.classList.contains('status')) {
      tekenMaatregelen();
      tekenDashboard();
    }
  }

  var SCOPE_KLASSE = {
    'In scope': 'vlag scope-in',
    'Buiten scope': 'vlag scope-buiten',
    'Nog te bepalen': 'vlag scope-nog',
    'Niet op dit niveau': 'vlag scope-niet'
  };

  function tekenMaatregelen() {
    var niveau = reken.effectief_niveau(dossier.instellingen, TABEL).effectief;
    var alleenGeldt = el('filter-geldt').checked;
    var filterScope = el('filter-scope').value;
    var filterParagraaf = el('filter-paragraaf').value;
    var filterStatus = el('filter-status').value;
    var zoek = el('zoek-maatregelen').value.trim().toLowerCase();
    var lijf = el('tabel-maatregelen').querySelector('tbody');
    var zichtbaar = 0;
    var perParagraaf = {};

    BRON.maatregelen.forEach(function (maatregel) {
      var tr = lijf.querySelector('[data-maatregel="' + maatregel.code + '"]');
      var regel = regelVan('maatregelen', maatregel.code);
      var geldt = reken.geldt(maatregel, niveau);
      var scope = reken.scope(maatregel, niveau, BRON.controls, dossier);

      tr.querySelector('[data-niveaus]').textContent = maatregel.niveaus.join(' ');
      tr.querySelector('.geldt').textContent = geldt ? 'Ja' : '—';
      var cel = tr.querySelector('.scope');
      cel.textContent = '';
      cel.appendChild(maak('span', scope, SCOPE_KLASSE[scope]));
      tr.querySelector('.status').value = regel.status || '';
      tr.querySelector('.bewijs').value = regel.bewijs || '';
      tr.querySelector('.verantwoordelijke').value = regel.verantwoordelijke || '';
      tr.querySelector('.opmerking').value = regel.opmerking || '';
      tr.className = geldt ? '' : 'grijs';

      var past = true;
      if (alleenGeldt && !geldt) past = false;
      if (past && filterScope && scope !== filterScope) past = false;
      if (past && filterParagraaf && maatregel.paragraaf !== filterParagraaf) past = false;
      if (past && filterStatus) {
        past = filterStatus === LEEG_STATUS ? !regel.status : regel.status === filterStatus;
      }
      if (past && zoek) {
        past = (maatregel.tekst + ' ' + maatregel.code + ' ' + maatregel.thema + ' ' +
          maatregel.groep).toLowerCase().indexOf(zoek) !== -1;
      }
      tr.hidden = !past;
      if (past) {
        zichtbaar += 1;
        perParagraaf[maatregel.paragraaf] = (perParagraaf[maatregel.paragraaf] || 0) + 1;
      }
    });

    BRON.paragrafen.forEach(function (paragraaf) {
      var koprij = lijf.querySelector('[data-paragraaf="' + paragraaf.id + '"]');
      var aantal = perParagraaf[paragraaf.id] || 0;
      koprij.hidden = aantal === 0;
      var opNiveau = BRON.maatregelen.filter(function (m) {
        return m.paragraaf === paragraaf.id && reken.geldt(m, niveau);
      }).length;
      koprij.querySelector('[data-partelling]').textContent =
        aantal + ' zichtbaar, ' + opNiveau + ' op niveau ' + niveau;
    });

    el('teller-maatregelen').textContent =
      zichtbaar + ' van ' + BRON.maatregelen.length + ' zichtbaar';
  }

  /* -------------------------------------------------------------- bijlagen */

  var BIJLAGE_KOPPEN = ['Bijlage', 'Titel', 'Type', 'Aangeroepen door', 'Van toepassing', 'Status',
    'Opmerking'];

  function bouwBijlagen() {
    var tabel = el('tabel-bijlagen');
    var kop = maak('thead');
    var koprij = maak('tr');
    BIJLAGE_KOPPEN.forEach(function (naam) {
      var th = maak('th', naam);
      th.setAttribute('scope', 'col');
      koprij.appendChild(th);
    });
    kop.appendChild(koprij);
    tabel.appendChild(kop);

    var lijf = maak('tbody');
    BRON.bijlagen.forEach(function (bijlage) {
      var tr = maak('tr');
      tr.setAttribute('data-bijlage', bijlage.id);
      tr.appendChild(maak('td', bijlage.id));
      tr.appendChild(maak('td', bijlage.titel));
      tr.appendChild(maak('td', bijlage.type));
      tr.appendChild(maak('td', bijlage.aangeroepen_door === null ? '—'
        : String(bijlage.aangeroepen_door)));

      var tdVt = maak('td');
      var vt = maak('select', null, 'vt');
      opties(vt, BRON.keuzes.van_toepassing, 'nog niet bepaald');
      tdVt.appendChild(vt);
      tr.appendChild(tdVt);

      var tdStatus = maak('td');
      var status = maak('select', null, 'status');
      opties(status, BRON.keuzes.status, 'nog geen status');
      tdStatus.appendChild(status);
      tr.appendChild(tdStatus);

      var tdOpmerking = maak('td');
      var opmerking = maak('input', null, 'opmerking');
      opmerking.type = 'text';
      tdOpmerking.appendChild(opmerking);
      tr.appendChild(tdOpmerking);
      lijf.appendChild(tr);
    });
    tabel.appendChild(lijf);

    tabel.addEventListener('change', function (g) { onBijlageWijziging(g.target); });
    tabel.addEventListener('input', function (g) {
      if (g.target.tagName === 'INPUT') onBijlageWijziging(g.target);
    });
  }

  function onBijlageWijziging(doel) {
    var tr = doel.closest ? doel.closest('tr[data-bijlage]') : null;
    if (!tr) return;
    var regel = regelVan('bijlagen', tr.getAttribute('data-bijlage'));
    if (doel.classList.contains('vt')) regel.vt = doel.value;
    else if (doel.classList.contains('status')) regel.status = doel.value;
    else if (doel.classList.contains('opmerking')) regel.opmerking = doel.value;
    else return;
    bewaar();
  }

  function tekenBijlagen() {
    var lijf = el('tabel-bijlagen').querySelector('tbody');
    BRON.bijlagen.forEach(function (bijlage) {
      var tr = lijf.querySelector('[data-bijlage="' + bijlage.id + '"]');
      var regel = regelVan('bijlagen', bijlage.id);
      tr.querySelector('.vt').value = regel.vt || '';
      tr.querySelector('.status').value = regel.status || '';
      tr.querySelector('.opmerking').value = regel.opmerking || '';
    });
  }

  /* ------------------------------------------------------------- dashboard */

  var RIJ_LABELS = [['vsp', 'VSP Proceseisen'], ['vse', 'VSE Systeemeisen'],
    ['maatregelen', 'Maatregelen'], ['totaal', 'Totaal']];
  var KOLOMMEN = [['vt', 'Van toepassing'], ['todo', 'Nog te doen'], ['bezig', 'In uitvoering'],
    ['klaar', 'Geïmplementeerd'], ['explain', 'Explain (afwijking)'], ['nvt', 'N.v.t.'],
    ['pct_impl', '% geïmpl.'], ['pct_afgeh', '% afgeh.']];

  function tellerCel(sleutel, waarde, isProcent) {
    var td = maak('td', isProcent ? procent(waarde) : String(waarde));
    td.setAttribute('data-teller', sleutel);
    return td;
  }

  function tekenDashboard() {
    var cijfers = reken.dashboard(BRON, dossier);
    var houder = el('dashboard-inhoud');
    houder.textContent = '';

    var kaart = maak('div', null, 'kaart');
    kaart.appendChild(maak('h2', 'Voortgang op niveau ' + cijfers.niveau));
    var tabel = maak('table', null, 'regels');
    var kop = maak('thead');
    var koprij = maak('tr');
    var leeg = maak('th', 'Onderdeel');
    leeg.setAttribute('scope', 'col');
    koprij.appendChild(leeg);
    KOLOMMEN.forEach(function (kolom) {
      var th = maak('th', kolom[1]);
      th.setAttribute('scope', 'col');
      koprij.appendChild(th);
    });
    kop.appendChild(koprij);
    tabel.appendChild(kop);

    var lijf = maak('tbody');
    RIJ_LABELS.forEach(function (paar) {
      var tr = maak('tr');
      var naam = paar[0] === 'maatregelen'
        ? 'Maatregelen (niv. ' + cijfers.niveau + ')' : paar[1];
      var th = maak('th', naam);
      th.setAttribute('scope', 'row');
      tr.appendChild(th);
      KOLOMMEN.forEach(function (kolom) {
        var isProcent = kolom[0].indexOf('pct') === 0;
        tr.appendChild(tellerCel(paar[0] + '.' + kolom[0], cijfers[paar[0]][kolom[0]], isProcent));
      });
      lijf.appendChild(tr);
    });
    tabel.appendChild(lijf);
    kaart.appendChild(tabel);
    houder.appendChild(kaart);

    var paneel = maak('div', null, 'paneel');

    var tegelControls = maak('div', null, 'tegel');
    tegelControls.appendChild(maak('h3', 'Van toepassing (alle ' + BRON.controls.length + ' controls)'));
    var lijstControls = maak('table', null, 'uitkomst');
    [['ja', 'Ja'], ['nee', 'Nee'], ['nvt', 'N.v.t. (buiten scope)'], ['leeg', 'Nog niet bepaald']]
      .forEach(function (paar) {
        var tr = maak('tr');
        var th = maak('th', paar[1]);
        th.setAttribute('scope', 'row');
        tr.appendChild(th);
        tr.appendChild(tellerCel('controls.' + paar[0], cijfers.controls[paar[0]], false));
        lijstControls.appendChild(tr);
      });
    tegelControls.appendChild(lijstControls);
    paneel.appendChild(tegelControls);

    var tegelScope = maak('div', null, 'tegel');
    tegelScope.appendChild(maak('h3', 'Scope van de maatregelen'));
    var lijstScope = maak('table', null, 'uitkomst');
    [['in', 'In scope'], ['buiten', 'Buiten scope'], ['nog', 'Nog te bepalen']]
      .forEach(function (paar) {
        var tr = maak('tr');
        var th = maak('th', paar[1]);
        th.setAttribute('scope', 'row');
        tr.appendChild(th);
        tr.appendChild(tellerCel('scope.' + paar[0], cijfers.scope[paar[0]], false));
        lijstScope.appendChild(tr);
      });
    tegelScope.appendChild(lijstScope);
    paneel.appendChild(tegelScope);
    houder.appendChild(paneel);

    var kaartPar = maak('div', null, 'kaart');
    kaartPar.appendChild(maak('h2', 'Per maatregelparagraaf'));
    var tabelPar = maak('table', null, 'regels');
    var kopPar = maak('thead');
    var koprijPar = maak('tr');
    ['Paragraaf', 'Thema', 'Op niveau', 'Geïmplementeerd', '%'].forEach(function (naam) {
      var th = maak('th', naam);
      th.setAttribute('scope', 'col');
      koprijPar.appendChild(th);
    });
    kopPar.appendChild(koprijPar);
    tabelPar.appendChild(kopPar);
    var lijfPar = maak('tbody');
    BRON.paragrafen.forEach(function (paragraaf) {
      var waarden = cijfers.paragraaf[paragraaf.id];
      var tr = maak('tr');
      tr.appendChild(maak('td', paragraaf.id));
      tr.appendChild(maak('td', paragraaf.thema));
      tr.appendChild(tellerCel('paragraaf.' + paragraaf.id + '.op_niveau', waarden.op_niveau, false));
      tr.appendChild(tellerCel('paragraaf.' + paragraaf.id + '.geimpl', waarden.geimpl, false));
      var pct = maak('td', waarden.pct === null ? '—' : procent(waarden.pct));
      pct.setAttribute('data-teller', 'paragraaf.' + paragraaf.id + '.pct');
      tr.appendChild(pct);
      lijfPar.appendChild(tr);
    });
    tabelPar.appendChild(lijfPar);
    kaartPar.appendChild(tabelPar);
    houder.appendChild(kaartPar);
  }

  /* --------------------------------------------------------------- uitdraai */

  function tabelVan(koppen, rijen) {
    var tabel = maak('table');
    var kop = maak('thead');
    var koprij = maak('tr');
    koppen.forEach(function (naam) {
      var th = maak('th', naam);
      th.setAttribute('scope', 'col');
      koprij.appendChild(th);
    });
    kop.appendChild(koprij);
    tabel.appendChild(kop);
    var lijf = maak('tbody');
    rijen.forEach(function (waarden) {
      var tr = maak('tr');
      waarden.forEach(function (waarde) { tr.appendChild(maak('td', waarde)); });
      lijf.appendChild(tr);
    });
    tabel.appendChild(lijf);
    return tabel;
  }

  function paarTabel(paren) {
    var tabel = maak('table');
    var lijf = maak('tbody');
    paren.forEach(function (paar) {
      var tr = maak('tr');
      var th = maak('th', paar[0]);
      th.setAttribute('scope', 'row');
      tr.appendChild(th);
      tr.appendChild(maak('td', paar[1] === '' || paar[1] === null ? '—' : String(paar[1])));
      lijf.appendChild(tr);
    });
    tabel.appendChild(lijf);
    return tabel;
  }

  function tekenUitdraai() {
    var houder = el('uitdraai-inhoud');
    houder.textContent = '';
    var niveauInfo = reken.effectief_niveau(dossier.instellingen, TABEL);
    var niveau = niveauInfo.effectief;
    var cijfers = reken.dashboard(BRON, dossier);
    var klas = reken.klassificeer(dossier.classificatie.scores, BRON.classificatie.ernst);

    houder.appendChild(maak('h2', 'Object en classificatie'));
    houder.appendChild(paarTabel([
      ['Organisatie', dossier.object.organisatie], ['Proces', dossier.object.proces],
      ['Object of objectgroep', dossier.object.naam], ['Locatie', dossier.object.locatie],
      ['Hoofdtaak', dossier.object.hoofdtaak], ['Ingevuld door', dossier.object.ingevuld_door],
      ['Team of afdeling', dossier.object.team], ['Datum', dossier.object.datum],
      ['Situatiebeschrijving', dossier.object.situatie]
    ]));
    houder.appendChild(tabelVan(['Criterium', 'Score', 'Ernst', 'Onderbouwing'],
      BRON.classificatie.criteria.map(function (criterium) {
        var score = dossier.classificatie.scores[criterium.id];
        var label = '';
        BRON.classificatie.ernst.forEach(function (e) { if (e.score === score) label = e.label; });
        return [criterium.titel, score === null || score === undefined ? '—' : String(score),
          label || '—', dossier.classificatie.onderbouwing[criterium.id] || '—'];
      })));
    houder.appendChild(paarTabel([
      ['Som van de zes scores', klas.compleet ? klas.som : 'nog niet compleet'],
      ['Afgerond gemiddelde', klas.compleet ? klas.gemiddelde + ' · ' + klas.gemiddelde_label : '—'],
      ['Functiebox uit de classificatie', klas.compleet ? klas.gemiddelde_functiebox : '—'],
      ['Weerstandsniveau uit de classificatie', klas.compleet ? klas.gemiddelde_niveau : '—'],
      ['Strengste lezing (hoogste score)', klas.compleet ? klas.hoogste + ' · ' +
        klas.hoogste_functiebox + ' · niveau ' + klas.hoogste_niveau : '—'],
      ['Opmerkingen', dossier.classificatie.opmerkingen]
    ]));

    houder.appendChild(maak('h2', 'Niveau en keten'));
    houder.appendChild(paarTabel([
      ['Functiebox', dossier.instellingen.functiebox || 'nog niet gekozen'],
      ['Herkomst functiebox', dossier.instellingen.functiebox_bron || '—'],
      ['Niveau uit de eigen functiebox', niveauInfo.eigen],
      ['Bedient of beheert andere objecten', dossier.instellingen.keten.actief ? 'Ja' : 'Nee'],
      ['Hoogste keten-niveau', niveauInfo.keten],
      ['Effectief weerstandsniveau', niveau + (niveauInfo.voorlopig ? ' (voorlopig)' : '')],
      ['Bevestigd door', dossier.instellingen.keten.bevestigd_door],
      ['Datum bevestiging', dossier.instellingen.keten.datum]
    ]));
    var ketenRijen = (dossier.instellingen.keten.objecten || []).filter(function (o) {
      return o && (o.naam || o.functiebox);
    }).map(function (o) {
      return [o.naam || '—', o.functiebox || '—',
        o.functiebox ? String(reken.niveau_van_functiebox(o.functiebox, TABEL).niveau) : '—'];
    });
    if (ketenRijen.length) {
      houder.appendChild(tabelVan(['Bediend of beheerd object', 'Functiebox', 'Niveau'], ketenRijen));
    }

    houder.appendChild(maak('h2', 'Dashboard'));
    houder.appendChild(tabelVan(
      ['Onderdeel'].concat(KOLOMMEN.map(function (k) { return k[1]; })),
      RIJ_LABELS.map(function (paar) {
        var naam = paar[0] === 'maatregelen' ? 'Maatregelen (niv. ' + niveau + ')' : paar[1];
        return [naam].concat(KOLOMMEN.map(function (kolom) {
          var waarde = cijfers[paar[0]][kolom[0]];
          return kolom[0].indexOf('pct') === 0 ? procent(waarde) : String(waarde);
        }));
      })));

    houder.appendChild(maak('h2', 'Controls die van toepassing zijn'));
    ['VSP', 'VSE'].forEach(function (blad) {
      var rijen = BRON.controls.filter(function (c) {
        return c.blad === blad && vanToepassing(dossier, 'controls', c.id) === 'Ja';
      }).map(function (c) {
        var regel = regelVan('controls', c.id);
        return [c.id, c.bio_bron, eisTekst(c), regel.status || '—', regel.bewijs || '—',
          regel.verantwoordelijke || '—'];
      });
      houder.appendChild(maak('h3', blad + ' · ' + rijen.length + ' van toepassing'));
      houder.appendChild(rijen.length
        ? tabelVan(['Control', 'BIO-bron', 'Eis', 'Status', 'Bewijs', 'Verantwoordelijke'], rijen)
        : maak('p', 'Geen enkele control op Ja.', 'leeg'));
    });

    var nietVan = BRON.controls.filter(function (c) {
      var vt = vanToepassing(dossier, 'controls', c.id);
      return vt && vt !== 'Ja';
    }).map(function (c) {
      var regel = regelVan('controls', c.id);
      return [c.id, c.bio_bron, regel.vt, regel.opmerking || '—'];
    });
    houder.appendChild(maak('h3', 'Niet van toepassing verklaard'));
    houder.appendChild(nietVan.length
      ? tabelVan(['Control', 'BIO-bron', 'Van toepassing', 'Onderbouwing'], nietVan)
      : maak('p', 'Alle controls zijn van toepassing verklaard.', 'leeg'));

    houder.appendChild(maak('h2', 'Maatregelen die gelden op niveau ' + niveau));
    BRON.paragrafen.forEach(function (paragraaf) {
      var rijen = BRON.maatregelen.filter(function (m) {
        return m.paragraaf === paragraaf.id && reken.geldt(m, niveau);
      }).map(function (m) {
        var regel = regelVan('maatregelen', m.code);
        return [m.code, m.tekst, reken.scope(m, niveau, BRON.controls, dossier),
          regel.status || '—', regel.bewijs || '—', regel.verantwoordelijke || '—'];
      });
      if (!rijen.length) return;
      houder.appendChild(maak('h3', paragraaf.id + ' · ' + paragraaf.thema +
        ' · ' + rijen.length));
      houder.appendChild(tabelVan(['Code', 'Maatregel', 'Scope', 'Status', 'Bewijs',
        'Verantwoordelijke'], rijen));
    });

    houder.appendChild(maak('h2', 'Afwijkingen (comply-or-explain)'));
    var afwijkingen = [];
    BRON.controls.forEach(function (c) {
      if (statusVan(dossier, 'controls', c.id) !== 'Explain (afwijking)') return;
      var regel = regelVan('controls', c.id);
      afwijkingen.push([c.id, 'Control', c.eis.slice(0, 200), regel.bewijs || '—',
        regel.opmerking || '—']);
    });
    BRON.maatregelen.forEach(function (m) {
      if (statusVan(dossier, 'maatregelen', m.code) !== 'Explain (afwijking)') return;
      var regel = regelVan('maatregelen', m.code);
      afwijkingen.push([m.code, 'Maatregel ' + m.paragraaf, m.tekst.slice(0, 200),
        regel.bewijs || '—', regel.opmerking || '—']);
    });
    BRON.bijlagen.forEach(function (b) {
      if (statusVan(dossier, 'bijlagen', b.id) !== 'Explain (afwijking)') return;
      var regel = regelVan('bijlagen', b.id);
      afwijkingen.push([b.id, 'Bijlage', b.titel, '—', regel.opmerking || '—']);
    });
    houder.appendChild(afwijkingen.length
      ? tabelVan(['Code', 'Soort', 'Tekst', 'Bewijs', 'Onderbouwing'], afwijkingen)
      : maak('p', 'Geen afwijkingen vastgelegd.', 'leeg'));

    houder.appendChild(maak('h2', 'Bijlagen'));
    houder.appendChild(tabelVan(['Bijlage', 'Titel', 'Type', 'Van toepassing', 'Status', 'Opmerking'],
      BRON.bijlagen.map(function (b) {
        var regel = regelVan('bijlagen', b.id);
        return [b.id, b.titel, b.type, regel.vt || '—', regel.status || '—',
          regel.opmerking || '—'];
      })));

    houder.appendChild(maak('h2', 'Verantwoording'));
    houder.appendChild(paarTabel([
      ['Bronversie', BRON.versie], ['Richtlijn', BRON.bron.richtlijn],
      ['Werkboekversie', BRON.bron.werkboek_versie],
      ['Vingerafdruk van de bron', BRON.vingerafdruk.slice(0, 16)],
      ['Dossier bijgewerkt', dossier.bijgewerkt || '—']
    ]));
    houder.appendChild(maak('p', BRON.bron.auteursrecht, 'klein'));
  }

  /* ------------------------------------------------------------- statusregel */

  function tekenStatusregel() {
    var uitkomst = reken.effectief_niveau(dossier.instellingen, TABEL);
    var delen = [];
    delen.push(dossier.object.naam ? 'Object: ' + dossier.object.naam
      : 'Nog geen object ingevuld');
    delen.push('niveau ' + uitkomst.effectief + (uitkomst.voorlopig ? ' (voorlopig)' : ''));
    if (dossier.bijgewerkt) delen.push('bijgewerkt ' + dossier.bijgewerkt.replace('T', ' '));
    var regel = el('dossier-status');
    regel.textContent = delen.join(' · ') + (melding ? ' · ' + melding : '');
    regel.className = melding ? 'let-op' : '';
  }

  /* ------------------------------------------------------------------ koppel */

  function koppelVeld(id, lees, schrijf, extra) {
    var veld = el(id);
    veld.addEventListener('input', function () {
      schrijf(veld.value);
      bewaar();
      if (extra) extra();
      tekenStatusregel();
    });
    veld.addEventListener('change', function () {
      schrijf(veld.value);
      bewaar();
      if (extra) extra();
      tekenStatusregel();
    });
    void lees;
  }

  function koppelObjectvelden() {
    [['obj-organisatie', 'organisatie'], ['obj-proces', 'proces'], ['obj-locatie', 'locatie'],
      ['obj-hoofdtaak', 'hoofdtaak'], ['obj-ingevuld-door', 'ingevuld_door'],
      ['obj-team', 'team'], ['obj-datum', 'datum'], ['obj-situatie', 'situatie']]
      .forEach(function (paar) {
        koppelVeld(paar[0], null, function (waarde) { dossier.object[paar[1]] = waarde; });
      });

    ['obj-naam', 'obj-naam-2'].forEach(function (id) {
      koppelVeld(id, null, function (waarde) { dossier.object.naam = waarde; }, function () {
        el('obj-naam').value = dossier.object.naam;
        el('obj-naam-2').value = dossier.object.naam;
        tekenControls('VSE');
      });
    });

    koppelVeld('klas-opmerkingen', null, function (waarde) {
      dossier.classificatie.opmerkingen = waarde;
    });

    koppelVeld('obj-functiebox', null, function (waarde) {
      dossier.instellingen.functiebox = waarde;
      dossier.instellingen.functiebox_bron = waarde ? 'handmatig' : '';
    }, function () {
      tekenInstellingen();
      tekenAlleTabellen();
    });

    koppelVeld('keten-actief', null, function (waarde) {
      dossier.instellingen.keten.actief = waarde === 'ja';
    }, function () {
      tekenInstellingen();
      tekenAlleTabellen();
    });

    koppelVeld('keten-bevestigd', null, function (waarde) {
      dossier.instellingen.keten.bevestigd_door = waarde;
    });
    koppelVeld('keten-datum', null, function (waarde) {
      dossier.instellingen.keten.datum = waarde;
    });

    el('keten-rijen').addEventListener('change', onKetenWijziging);
    el('keten-rijen').addEventListener('input', onKetenWijziging);
  }

  function onKetenWijziging(gebeurtenis) {
    var doel = gebeurtenis.target;
    var index = doel.getAttribute('data-keten-naam') || doel.getAttribute('data-keten-fb');
    if (!index) return;
    var object = dossier.instellingen.keten.objecten[parseInt(index, 10) - 1];
    if (doel.hasAttribute('data-keten-naam')) object.naam = doel.value;
    else object.functiebox = doel.value;
    bewaar();
    tekenInstellingen();
    tekenAlleTabellen();
    tekenStatusregel();
  }

  /* ------------------------------------------------------------------ tekenen */

  function tekenAlleTabellen() {
    tekenControls('VSP');
    tekenControls('VSE');
    tekenMaatregelen();
    tekenBijlagen();
    tekenDashboard();
  }

  function tekenAlles() {
    el('obj-organisatie').value = dossier.object.organisatie || '';
    el('obj-proces').value = dossier.object.proces || '';
    el('obj-naam').value = dossier.object.naam || '';
    el('obj-locatie').value = dossier.object.locatie || '';
    el('obj-hoofdtaak').value = dossier.object.hoofdtaak || '';
    el('obj-ingevuld-door').value = dossier.object.ingevuld_door || '';
    el('obj-team').value = dossier.object.team || '';
    el('obj-datum').value = dossier.object.datum || '';
    el('obj-situatie').value = dossier.object.situatie || '';
    tekenClassificatie();
    tekenInstellingen();
    tekenAlleTabellen();
    tekenStatusregel();
    if (!el('scherm-uitdraai').hidden) tekenUitdraai();
  }

  /* --------------------------------------------------------------------- start */

  function start() {
    el('versie').textContent = 'bronversie ' + BRON.versie + ', werkboek ' +
      BRON.bron.werkboek_versie;
    el('auteursrecht').textContent = BRON.bron.auteursrecht;
    el('klas-toelichting').textContent = BRON.classificatie.toelichting_rekenregel;

    bouwClassificatie();
    bouwInstellingen();
    bouwControls('VSP');
    bouwControls('VSE');
    bouwMaatregelen();
    bouwBijlagen();
    koppelObjectvelden();

    SCHERMEN.forEach(function (naam) {
      el('tab-' + naam).addEventListener('click', function () { toon(naam); });
    });

    ['zoek-vsp', 'zoek-vse'].forEach(function (id) {
      el(id).addEventListener('input', function () {
        tekenControls(id === 'zoek-vsp' ? 'VSP' : 'VSE');
      });
    });
    ['filter-geldt', 'filter-scope', 'filter-paragraaf', 'filter-status', 'zoek-maatregelen']
      .forEach(function (id) {
        el(id).addEventListener('change', tekenMaatregelen);
        el(id).addEventListener('input', tekenMaatregelen);
      });

    el('knop-classificatie-overnemen').addEventListener('click', function () {
      var uitkomst = reken.klassificeer(dossier.classificatie.scores, BRON.classificatie.ernst);
      if (!uitkomst.compleet) return;
      dossier.instellingen.functiebox = uitkomst.gemiddelde_functiebox;
      dossier.instellingen.functiebox_bron = 'classificatie';
      bewaar();
      tekenAlles();
      toon('instellingen');
    });

    el('knop-opslaan').addEventListener('click', opslaanAlsBestand);
    el('knop-laden').addEventListener('click', function () { el('bestand-laden').click(); });
    el('bestand-laden').addEventListener('change', function (gebeurtenis) {
      var bestand = gebeurtenis.target.files && gebeurtenis.target.files[0];
      if (bestand) ladenUitBestand(bestand);
      gebeurtenis.target.value = '';
    });
    el('knop-afdrukken').addEventListener('click', function () {
      toon('uitdraai');
      window.print();
    });
    el('knop-wissen').addEventListener('click', function () {
      if (!window.confirm('Het hele dossier wissen? Dit kan niet ongedaan worden gemaakt.')) return;
      try {
        window.localStorage.removeItem(OPSLAG);
      } catch (fout) {
        melding = 'Wissen uit de browseropslag lukte niet.';
      }
      dossier = reken.nieuw_dossier(BRON);
      tekenAlles();
    });
    window.addEventListener('beforeprint', tekenUitdraai);

    toon('classificatie');
    tekenAlles();
  }

  start();
}());
