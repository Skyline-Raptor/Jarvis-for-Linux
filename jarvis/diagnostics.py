import importlib.util
from .config import hardware


def report(config,model,accounts=None,mesh=None):
    result=hardware(config.home)
    try:
        result['installed_models']=model.available()
    except Exception as e:
        result['model_error']=str(e)
    result.update(chat_model=config.get('model'),vision_model=config.get('vision_model'),roots=config.get('roots'),
                  observation=config.get('observe'),wake=config.get('wake'),voice=config.get('voice'))
    result['modules']={name:importlib.util.find_spec(name) is not None for name in ('PySide6','docx','openpyxl','pptx','pypdf','sounddevice','kokoro_onnx','faster_whisper','mss','ddgs')}
    result['voice_assets']={f:(config.home/'Models'/'Voice'/f).is_file() for f in ('kokoro-v1.0.onnx','voices-v1.0.bin')}
    result['accounts']={p:bool(accounts and accounts.vault.get(p)) for p in ('google','microsoft')}
    result['peers']=list(mesh.data['peers']) if mesh else []
    result['comfy_workflow']=bool(config.get('comfy_workflow'))
    from .linux_desktop import session_type
    result['desktop_session']=session_type()
    result['native_validation']='Inventory only; test real microphone, screen, accounts and GPU on your computer'
    return result
