import fs from 'fs'
import os from 'os'
import path from 'path'
import { inc as semverInc } from 'semver'

import root from './root'
import { ContinuousIntegration as CI } from './continuous-integration'

let version: string = null

const version_js = path.join(root, 'gen/version.js')
if (fs.existsSync(version_js)) {
  version = (require(version_js) as string)
}
else {
  console.log('Writing version')

  version = require(path.join(root, 'package.json')).version

  if (CI.service && !CI.tag) {
    version = `${semverInc(version, 'patch')}-${CI.build_number}`
  }
  else if (!CI.service) {
    version = `${semverInc(version, 'patch')}-${os.userInfo().username}.${os.hostname()}`
  }

  if (!fs.existsSync(path.dirname(version_js))) fs.mkdirSync(path.dirname(version_js))
  fs.writeFileSync(version_js, `module.exports = ${JSON.stringify(version)};\n`, 'utf8')
}

export default version
