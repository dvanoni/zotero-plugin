import fse from 'fs-extra'
import path from 'path'

import root from './root'

const IGNORED_EXTENSIONS = ['.json', '.ts', '.tsx']

const IGNORED_PATHS = /(\.DS_Store|__tests__)$/

const srcDir = path.join(root, 'src')
const destDir = path.join(root, 'build')

console.group('Copying assets')

fse.copySync(srcDir, destDir, {
  filter(src) {
    const include = (
      !IGNORED_EXTENSIONS.includes(path.extname(src).toLowerCase()) &&
      !IGNORED_PATHS.test(src)
    )
    if (include) console.log(src)
    return include
  }
})

console.groupEnd()
