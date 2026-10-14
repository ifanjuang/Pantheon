(function (global) {
  "use strict";

  const rootNode = document.getElementById("plugin-root");
  const React = global.React;
  const ReactDOM = global.ReactDOM;
  let fixturePromise = null;

  function fixture() {
    if (!fixturePromise) {
      fixturePromise = fetch("hermes-modules-demo.json", { cache: "no-store" })
        .then(function (response) {
          if (!response.ok) throw new Error("Demo fixture unavailable (" + response.status + ")");
          return response.json();
        })
        .then(function (data) {
          if (!data.meta || data.meta.synthetic !== true) {
            throw new Error("Demo fixture rejected: meta.synthetic must be true");
          }
          return data;
        });
    }
    return fixturePromise;
  }

  function payload(name) {
    return fixture().then(function (data) { return data.payloads[name]; });
  }

  function element(tag, defaultClass) {
    return function Component(props) {
      const next = Object.assign({}, props);
      const children = next.children;
      delete next.children;
      if (defaultClass) next.className = [defaultClass, next.className].filter(Boolean).join(" ");
      return React.createElement(tag, next, children);
    };
  }

  function SafeButton(props) {
    const next = Object.assign({}, props, {
      disabled: true,
      title: "Démonstration : action désactivée",
      "aria-disabled": "true"
    });
    delete next.variant;
    return React.createElement("button", next, props.children);
  }

  const components = {
    Button: SafeButton,
    Input: element("input", "pm-demo-input"),
    Card: element("article", "pm-card"),
    CardHeader: element("header", "pm-card-header"),
    CardTitle: element("h3", "pm-card-title"),
    CardContent: element("div", "pm-card-content"),
    Badge: function Badge(props) {
      const next = Object.assign({}, props);
      delete next.variant;
      return React.createElement("span", next, props.children);
    }
  };

  const readApi = {
    getMemory: function () { return payload("memory"); },
    getMcpCatalog: function () { return payload("catalog"); },
    getMcpServers: function () { return payload("servers"); },
    getPluginsHub: function () { return payload("hub"); },
    getCronJobs: function () { return payload("jobs"); }
  };

  [
    "setMemoryProvider", "enableAgentPlugin", "disableAgentPlugin",
    "setMcpServerEnabled", "testMcpServer", "installMcpCatalogEntry"
  ].forEach(function (name) {
    readApi[name] = function () {
      return Promise.reject(new Error("Démonstration : mutation Hermes désactivée (" + name + ")"));
    };
  });

  global.confirm = function () { return false; };
  global.__HERMES_PLUGIN_SDK__ = {
    mode: "demo",
    React: React,
    hooks: React,
    components: components,
    api: readApi
  };
  global.__HERMES_PLUGINS__ = {
    register: function (_name, Page) {
      ReactDOM.createRoot(rootNode).render(React.createElement(Page));
    }
  };
})(window);
