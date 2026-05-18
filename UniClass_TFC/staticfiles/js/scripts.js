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
