import { createApp } from "vue";
import { createLogto } from "@logto/vue";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import App from "./App.vue";
import { logtoApiResource, logtoAppId, logtoEndpoint } from "./api/http";
import router from "./router";
import "./styles/index.css";

createApp(App)
  .use(createLogto, {
    endpoint: logtoEndpoint,
    appId: logtoAppId,
    scopes: [
      "read:images",
      "upload:images",
      "review:reports",
      "finalize:reports",
    ],
    resources: [logtoApiResource],
  })
  .use(ElementPlus)
  .use(router)
  .mount("#app");
