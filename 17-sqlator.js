const form = document.getElementById('form');
const responseDiv1 = document.getElementById('response1');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  responseDiv1.innerHTML = '<h1>OK:</h1><div class="loader"></div>';
  const question = document.getElementById('question').value;
  
  const eventSource = new EventSource('/respond?question=' + encodeURIComponent(question));
  
  eventSource.onmessage = (event) => {
    responseDiv1.querySelector('.loader').style.display = 'none';
    const formattedData = event.data.replace(/\n/g, '<br>');
    responseDiv1.innerHTML += formattedData;

    console.log(event);
  };
  
  eventSource.onerror = () => {
    console.log('error');
    
    document.getElementById('content-container').innerHTML = 'Loading...';
    setTimeout(() => {
      fetch(window.location.href)
        .then(response => response.text())
        .then(html => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          
          const newContentContainer = doc.getElementById('content-container');
          const newTableContainer = doc.getElementById('table-container');
          
          if (newContentContainer) {
            document.getElementById('content-container').innerHTML = newContentContainer.innerHTML;
          }
          if (newTableContainer) {
            document.getElementById('table-container').innerHTML = newTableContainer.innerHTML;
          }
        })
        .catch(error => console.error('Error refreshing content:', error));
    }, 2000);
    eventSource.close();
  };
}); 