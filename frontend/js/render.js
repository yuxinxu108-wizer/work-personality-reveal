export function setText(id, value) {
  document.getElementById(id).textContent = value;
}


export function clear(node) {
  node.textContent = "";
}


export function renderApiError(message) {
  const optionsList = document.getElementById("optionsList");
  optionsList.textContent = message;
}
