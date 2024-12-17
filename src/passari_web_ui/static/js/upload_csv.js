document.getElementById('csv_file').addEventListener('change', function (event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (e) {
    const content = e.target.result;
    const lines = content.split(/[\r\n]+/).filter(line => line.trim() !== "");
    const objectIDs = lines.join("\n");
    document.getElementById('object_ids').value = objectIDs;
  };

  reader.onerror = function () {
    alert("Error reading the file. Please make sure it is a valid CSV file.");
  };

  reader.readAsText(file);
});
