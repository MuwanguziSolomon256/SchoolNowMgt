document.addEventListener('DOMContentLoaded', function(){
  const btn = document.getElementById('snm-logout-btn');
  const modal = document.getElementById('snm-logout-modal');
  const cancel = document.getElementById('snm-logout-cancel');
  const confirm = document.getElementById('snm-logout-confirm');
  const form = document.getElementById('snm-logout-form');

  if(!btn) return;
  btn.addEventListener('click', function(e){
    e.preventDefault();
    if(modal) modal.classList.remove('hidden');
  });

  if(cancel){
    cancel.addEventListener('click', function(){ if(modal) modal.classList.add('hidden'); });
  }
  if(confirm){
    confirm.addEventListener('click', function(){
      if(form) form.submit();
    });
  }
});
