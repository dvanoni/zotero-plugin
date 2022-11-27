import fse from 'fs-extra'
import path from 'path'

import root from './root'

const IGNORED_EXTENSIONS = ['.json', '.ts']

function includeFile(src: string) {
  const include = !IGNORED_EXTENSIONS.includes(path.extname(src).toLowerCase())
  if (include) console.log(src)
  return include
}

const srcDir = path.join(root, 'src')
const destDir = path.join(root, 'build')

console.group('Copying assets')

fse.copySync(srcDir, destDir, { filter: includeFile })

console.groupEnd()
