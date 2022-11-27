import fse from 'fs-extra'
import path from 'path'
import pug from 'pug'

import root from './root'
import version from './version'

const BUILD_DIR = 'build'
const INSTALL_RDF_PATH = `${BUILD_DIR}/install.rdf`
const MANIFEST_JSON_PATH = `${BUILD_DIR}/manifest.json`

const pkg = { ...require(path.join(root, 'package.json')) }

if (!pkg.id) {
  (pkg.id as string) = `${pkg.name.replace(
    /^zotero-/,
    ''
  )}@${pkg.author.email.replace(/.*@/, '')}`.toLowerCase()
}
if (pkg.xpi) Object.assign(pkg, pkg.xpi)

pkg.version = version

pkg.updateURL = `${pkg.xpi.releaseURL}update.rdf`

const options_and_vars = { ...pkg, pretty: true }

console.log(`Generating ${INSTALL_RDF_PATH}`)

const template = fse.readFileSync(
  path.join(__dirname, 'install.rdf.pug'),
  'utf8'
)
const installRdf = pug.render(template, options_and_vars)
fse.outputFileSync(path.join(root, INSTALL_RDF_PATH), installRdf)

console.log(`Generating ${MANIFEST_JSON_PATH}`)

const manifestJson = {
  manifest_version: 2,
  name: pkg.name,
  description: pkg.description,
  version: pkg.version,
  homepage_url: pkg.homepage,
  applications: {
    zotero: {
      id: pkg.id,
      update_url: `${pkg.xpi.releaseURL}updates.json`,
      strict_min_version: '6.999',
      strict_max_version: '7.0.*',
    },
  },
}

fse.outputJsonSync(
  path.join(root, MANIFEST_JSON_PATH),
  manifestJson,
  { spaces: 2 }
)
