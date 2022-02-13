#!/usr/bin/env python3

import os, sys
import shutil
import json
import configparser
import glob
import shlex
import xml.etree.ElementTree as ET
import subprocess
import collections
import types
import platform

class Config:
  def __init__(self):
    config_file = 'zotero-plugin.ini'
    assert os.path.isfile(config_file), f'cannot find {config_file}'

    config = configparser.ConfigParser(strict = False)
    config.read(config_file)

    self.profile = types.SimpleNamespace(
      path=os.path.expanduser(config.get('profile', 'path')),
      name=config.get('profile', 'name', fallback=None)
    )

    self.zotero = types.SimpleNamespace(
      path=config.get('zotero', 'path', fallback=None),
      log=config.get('zotero', 'log', fallback=None),
      db=config.get('zotero', 'db', fallback=None)
    )

    if self.zotero.path:
      self.zotero.path = os.path.expanduser(self.zotero.path)
    elif platform.system() == 'Darwin':
      self.zotero.path = '/Applications/Zotero.app/Contents/MacOS/zotero'
    elif platform.system() == 'Linux':
      self.zotero.path = '/usr/lib/zotero/zotero'
    elif platform.system() == 'Windows':
      self.zotero.path = 'C:/Program Files (x86)/Zotero/Zotero.exe'
    else:
      assert False, f'{platform.system()} not supported'
      
    if self.zotero.log:
      self.zotero.log = os.path.expanduser(self.zotero.log)

    self.plugin = types.SimpleNamespace(
      source=os.path.abspath(config.get('plugin', 'source', fallback=self.find_source())),
      build=config.get('plugin', 'build', fallback='npm run build')
    )

    if 'preferences' in config:
      self.preference = { k: self.pref_value(v) for k, v in dict(config['preferences']).items() }
    else:
      self.preference = {}

    # always set these
    self.preference['extensions.autoDisableScopes']= 0
    self.preference['extensions.enableScopes'] = 15
    self.preference['extensions.startupScanScopes'] = 15
    self.preference['extensions.zotero.debug.log'] = True
    # null deletes if present
    self.preference['extensions.lastAppBuildId'] = None
    self.preference['extensions.lastAppVersion'] = None

  def find_source(self):
    for rdf in glob.glob(os.path.join('*', 'install.rdf')):
      return os.path.dirname(rdf)
    if os.path.isdir('build'):
      return 'build'
    return False

  def pref_value(self, v):
    if v in ['true', 'false']: return v == 'true'
    if v == 'null': return None
    try:
      return int(v)
    except ValueError:
      pass
    try:
      return float(v)
    except ValueError:
      pass
    try:
      return json.loads(v)
    except json.decoder.JSONDecodeError:
      pass
    return v
config = Config()

def patch_prefs(prefs, add_config):
  def name(line):
    if not line.startswith('user_pref('): return None
    if not line.startswith('user_pref("'): raise ValueError('unexpected user pref: ' + line)
    open_quote = None
    for i, c in enumerate(line):
      if c == '"':
        if open_quote is None:
          open_quote = i
        else:
          try:
            return json.loads(line[open_quote : i + 1])
          except json.decoder.JSONDecodeError:
            pass
    raise ValueError('unexpected user pref: ' + line)

  prefs = os.path.join(config.profile.path, f'{prefs}.js')
  if not os.path.exists(prefs): return

  user_prefs = []
  with open(prefs) as f:
    for line in f.readlines():
      if name(line) not in config.preference:
        user_prefs.append(line)
    if add_config:
      for key, value in config.preference.items():
        if value is not None:
          user_prefs.append(f'user_pref({json.dumps(key)}, {json.dumps(value)});\n')

  with open(prefs, 'w') as f:
    f.write(''.join(user_prefs))

patch_prefs('prefs', False)
patch_prefs('user', True)

def system(cmd):
  print('$', cmd)
  subprocess.run(cmd, shell=True, check=True)

if config.plugin.build:
  system(config.plugin.build)

if config.zotero.db:
  shutil.copyfile(config.zotero.db, os.path.join(config.profile.path, 'zotero', 'zotero.sqlite'))

# check if the system is windows
is_windows = platform.system() == 'Windows'

for plugin_id in ET.parse(os.path.join(config.plugin.source, 'install.rdf')).getroot().findall('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description/{http://www.mozilla.org/2004/em-rdf#}id'):
  plugin_path = os.path.join(config.profile.path, 'extensions', plugin_id.text)
with open(plugin_path, 'w') as f:
  sources = config.plugin.source
  if sources[-1] != '/': sources += '/'

  if is_windows:
    sources = sources.replace('\\', '\\\\').replace('/', '\\\\')

  print('Writing addon source path to proxy file')
  print('Source path: ' + sources)
  print('Proxy file path: ' + plugin_path)

  print(sources, file=f)


# wrap zotero.exe with double quotes, otherwise cmd will fail to parse path with spaces.
if is_windows:
    config.zotero.path = "\"" + config.zotero.path + "\""

cmd = config.zotero.path + ' -purgecaches -P'
if config.profile.name: cmd += ' ' + shlex.quote(config.profile.name)

# per https://www.zotero.org/support/debug_output, use ZoteroDebug instead of ZOteroDebugText for windows
debug_flag = '-ZoteroDebugText'
if is_windows:
  debug_flag = '-ZoteroDebug'

cmd += ' -jsconsole ' + debug_flag + ' -datadir profile'
if config.zotero.log: cmd += ' > ' + shlex.quote(config.zotero.log)
cmd += ' &'

system(cmd)
