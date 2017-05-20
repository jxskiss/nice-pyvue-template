The vue components stays here.


The components can be imported by three ways:

1. use relative path:

   `import AwsomeComponent from '../../components/AwsomeComponent.vue`

2. use components/AwesomeComponent.vue directly:

   `import AwesomeComponent from 'components/AwesomeComponent.vue`

3. use @ to indicate local files:

   `import AwesomeComponent from '@/components/AwesomeComponent.vue`,

   this is the default way used by vue-cli webpack template.


See webpack.config.js for more details about path resolving.
