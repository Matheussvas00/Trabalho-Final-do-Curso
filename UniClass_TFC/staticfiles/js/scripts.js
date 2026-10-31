/**
 * UniClass - Scripts Customizados
 */

// Auto-dismiss alerts após 5 segundos
document.addEventListener("DOMContentLoaded", function () {
  const alerts = document.querySelectorAll(".alert");

  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
});

// Validação de email em tempo real (opcional)
const emailInput = document.querySelector('input[type="email"]');
if (emailInput) {
  emailInput.addEventListener("blur", function () {
    const email = this.value.toLowerCase();
    const isAluno = email.endsWith("@academico.unirv.edu.br");
    const isStaff = email.endsWith("@unirv.edu.br");

    if (email && !isAluno && !isStaff) {
      this.classList.add("is-invalid");
    } else {
      this.classList.remove("is-invalid");
    }
  });
}

// ─────────────────────────────────────────────────────────
// ucSearch — Busca em tempo real para tabelas CRUD
// tableId   : id da <table>
// inputId   : id do <input> de busca
// counterId : id do elemento que mostra a contagem (opcional)
// ─────────────────────────────────────────────────────────
function ucSearch(tableId, inputId, counterId) {
  var input = document.getElementById(inputId);
  var table = document.getElementById(tableId);
  if (!input || !table) return;

  function normalize(str) {
    return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  var query = normalize(input.value.toLowerCase().trim());
  var rows = table.querySelectorAll("tbody tr");
  var visible = 0;

  rows.forEach(function (row) {
    var text = normalize(row.textContent.toLowerCase());
    var show = !query || text.indexOf(query) !== -1;
    row.style.display = show ? "" : "none";
    if (show) visible++;
  });

  // Mostra/oculta linha de "nenhum resultado"
  var emptyRow = document.getElementById(tableId + "-empty");
  if (emptyRow) {
    emptyRow.style.display = visible === 0 ? "" : "none";
  }

  // Atualiza contador
  if (counterId) {
    var counter = document.getElementById(counterId);
    if (counter) counter.textContent = visible;
  }

  // Botão limpar
  var clearBtn = document.getElementById(inputId + "-clear");
  if (clearBtn) {
    clearBtn.style.display = query ? "flex" : "none";
  }
}

// Bind automático: qualquer input com data-search-table inicializa sozinho
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-search-table]").forEach(function (input) {
    var tableId = input.getAttribute("data-search-table");
    var counterId = input.getAttribute("data-search-counter") || null;
    input.addEventListener("input", function () {
      ucSearch(tableId, input.id, counterId);
    });
    // Botão limpar via data-clear-for
    var clearBtn = document.getElementById(input.id + "-clear");
    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        input.value = "";
        ucSearch(tableId, input.id, counterId);
        input.focus();
      });
    }
  });
});

// ─────────────────────────────────────────────────────────
// ucToggleTheme — Alterna entre modo claro e escuro
// O tema inicial é aplicado no <head> do base.html
// ─────────────────────────────────────────────────────────
function ucToggleTheme() {
  var html = document.documentElement;
  var tema = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", tema);
  html.setAttribute("data-bs-theme", tema);
  try {
    localStorage.setItem("uc-theme", tema);
  } catch (e) {}
}

// ─────────────────────────────────────────────────────────
// ucDiscPicker — lista de disciplinas com busca, contador e
// "marcar/desmarcar todas" (modais de aluno, professor e portaria)
// ─────────────────────────────────────────────────────────
(function () {
  function normalizar(texto) {
    return (texto || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function remover(lista) {
    if (!lista) return;
    if (lista._ucBar) { lista._ucBar.remove(); lista._ucBar = null; }
    if (lista._ucChange) { lista.removeEventListener("change", lista._ucChange); lista._ucChange = null; }
    var vazio = lista.querySelector(".uc-disc-picker__vazio");
    if (vazio) vazio.remove();
  }

  function ucDiscPicker(lista) {
    if (!lista) return;
    remover(lista);
    lista.style.display = "";
    var opcoes = Array.prototype.slice.call(lista.querySelectorAll(".uc-disc-opt"));
    if (!opcoes.length) return;

    var barra = document.createElement("div");
    barra.className = "uc-disc-picker__bar";

    var busca = null;
    if (opcoes.length > 6) {
      var caixa = document.createElement("div");
      caixa.className = "uc-disc-picker__busca";
      caixa.innerHTML = '<i class="fas fa-search"></i>';
      busca = document.createElement("input");
      busca.type = "search";
      busca.placeholder = "Buscar disciplina...";
      busca.setAttribute("aria-label", "Buscar disciplina");
      caixa.appendChild(busca);
      barra.appendChild(caixa);
    }

    var acoes = document.createElement("div");
    acoes.className = "uc-disc-picker__acoes";
    var contador = document.createElement("span");
    contador.className = "uc-disc-picker__count";
    var todas = document.createElement("button");
    todas.type = "button";
    todas.className = "uc-disc-picker__link";
    todas.textContent = "Marcar todas";
    var nenhuma = document.createElement("button");
    nenhuma.type = "button";
    nenhuma.className = "uc-disc-picker__link";
    nenhuma.textContent = "Desmarcar";
    acoes.appendChild(contador);
    acoes.appendChild(todas);
    acoes.appendChild(nenhuma);
    barra.appendChild(acoes);

    lista.parentNode.insertBefore(barra, lista);
    lista._ucBar = barra;

    var vazio = document.createElement("div");
    vazio.className = "uc-disc-picker__vazio";
    vazio.textContent = "Nenhuma disciplina encontrada.";
    vazio.hidden = true;
    lista.appendChild(vazio);

    function atualizar() {
      var marcadas = lista.querySelectorAll(".uc-disc-opt__input:checked").length;
      contador.textContent = marcadas + " de " + opcoes.length + (marcadas === 1 ? " selecionada" : " selecionadas");
    }

    function marcar(valor) {
      opcoes.forEach(function (opcao) {
        if (opcao.classList.contains("is-oculta")) return;
        var input = opcao.querySelector(".uc-disc-opt__input");
        if (input && input.checked !== valor) {
          input.checked = valor;
          input.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
      atualizar();
    }

    todas.addEventListener("click", function () { marcar(true); });
    nenhuma.addEventListener("click", function () { marcar(false); });

    if (busca) {
      busca.addEventListener("input", function () {
        var termo = normalizar(busca.value.trim());
        var visiveis = 0;
        opcoes.forEach(function (opcao) {
          var ok = !termo || normalizar(opcao.textContent).indexOf(termo) !== -1;
          opcao.classList.toggle("is-oculta", !ok);
          if (ok) visiveis++;
        });
        vazio.hidden = visiveis > 0;
      });
      // Enter na busca não envia o formulário
      busca.addEventListener("keydown", function (e) { if (e.key === "Enter") e.preventDefault(); });
    }

    // form.reset() não dispara "change": recalcula o contador depois de limpar o formulário
    var formulario = lista.closest("form");
    if (formulario && !formulario._ucResetDisc) {
      formulario._ucResetDisc = true;
      formulario.addEventListener("reset", function () {
        setTimeout(function () {
          formulario.querySelectorAll(".uc-disc-picker__list").forEach(function (l) {
            if (l._ucChange) l._ucChange();
          });
        });
      });
    }

    lista._ucChange = atualizar;
    lista.addEventListener("change", atualizar);
    atualizar();
  }

  ucDiscPicker.remover = remover;
  window.ucDiscPicker = ucDiscPicker;

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".uc-disc-picker__list").forEach(function (lista) {
      ucDiscPicker(lista);
    });
  });
})();
