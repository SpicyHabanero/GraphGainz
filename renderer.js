reconst { PythonShell } = require('python-shell');
const pdfjsLib = require('pdfjs-dist');
const { dialog } = require('electron').remote;

let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;

const scale = 1;
const canvas = document.getElementById('pdf-canvas');
const ctx = canvas.getContext('2d');

function renderPage(num) {
  pageRendering = true;
  pdfDoc.getPage(num).then((page) => {
    const viewport = page.getViewport({ scale });
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
      canvasContext: ctx,
      viewport: viewport,
    };

    const renderTask = page.render(renderContext);

    renderTask.promise.then(() => {
      pageRendering = false;
      if (pageNumPending !== null) {
        renderPage(pageNumPending);
        pageNumPending = null;
      }
    });
  });

  document.getElementById('page_num').textContent = num;
}

function queueRenderPage(num) {
  if (pageRendering) {
    pageNumPending = num;
  } else {
    renderPage(num);
  }
}

function onPrevPage() {
  if (pageNum <= 1) {
    return;
  }
  pageNum--;
  queueRenderPage(pageNum);
}

function onNextPage() {
  if (pageNum >= pdfDoc.numPages) {
    return;
  }
  pageNum++;
  queueRenderPage(pageNum);
}

document.getElementById('prev').addEventListener('click', onPrevPage);
document.getElementById('next').addEventListener('click', onNextPage);

function handleFile(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    alert('Please select a PDF file');
    return;
  }

  PythonShell.run(
    '/Users/eddiegarcia/Desktop/GraphGainz/testkgp.py',
    { args: [file.path] },
    (err, results) => {
      if (err) {
        console.error(err);
        alert('An error occurred while executing the Python script');
        return;
      }
      console.log('Python script executed successfully');
      console.log('Python script results:', results);

      const fileReader = new FileReader();

      fileReader.onload = (event) => {
        const typedArray = new Uint8Array(event.target.result);
        pdfjsLib.getDocument(typedArray).promise.then((pdf) => {
          pdfDoc = pdf;
          document.getElementById('page_count').textContent = pdf.numPages;
          renderPage(pageNum);
        });
      };

      fileReader.readAsArrayBuffer(file);
    }
  );
}

const dropzone = document.getElementById('dropzone');

dropzone.addEventListener('dragover', (event) => {
  event.preventDefault();
  event.stopPropagation();
  event.dataTransfer.dropEffect = 'copy';
});

dropzone.addEventListener('drop', (event) => {
  event.preventDefault();
  event.stopPropagation();
  console.log('File dropped:', event.dataTransfer.files[0]);
  handleFile(event.dataTransfer.files[0]);
});

dropzone.addEventListener('click', () => {
    dialog
      .showOpenDialog({
        properties: ['openFile'],
        filters: [{ name: 'PDF Files', extensions: ['pdf'] }],
      })
      .then((result) => {
        if (!result.canceled && result.filePaths.length > 0) {
          handleFile(new File(result.filePaths, 'selected.pdf'));
        }
      });      
});
  
document.getElementById('open-file').addEventListener('click', () => {
    dialog
        .showOpenDialog({
        properties: ['openFile'],
        filters: [{ name: 'PDF Files', extensions: ['pdf'] }],
      })
      .then((result) => {
        if (!result.canceled && result.filePaths.length > 0) {
          handleFile(new File(result.filePaths, 'selected.pdf'));
        }
      });
});

document.getElementById('open-file').addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFile(file);
    }
});

openFile.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/process-pdf', {
    method: 'POST',
    body: formData,
  });

  if (response.ok) {
    const answers = await response.json();
    console.log('Answers:', answers);
  } else {
    console.error('File processing failed');
  }
  
});openFile.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/process-pdf', {
    method: 'POST',
    body: formData,
  });

  if (response.ok) {
    const answers = await response.json();
    console.log('Answers:', answers);
  } else {
    console.error('File processing failed');
  }
});
