export default async function BrowserOptimizationPlugin() {
  return {
    name: "browser-optimization",
    hooks: {
      "chat.send.before": async (context) => {
        // Inyectamos una directiva oculta en el sistema antes de enviar el mensaje al modelo
        const optimizationPrompt = `
[Plugin Browser-Optimization Activo]: Cuando uses las herramientas de Playwright/Browser:
1. Reutiliza el contexto de navegación existente o pestañas abiertas si es posible.
2. No solicites capturas de pantalla (screenshots) a menos que la tarea requiera explícitamente inspección visual o de diseño. Preferiblemente lee el texto o la estructura DOM.
3. Sé conciso al navegar para ahorrar recursos de red.
`;
        
        // Añadimos la instrucción al inicio del mensaje del sistema
        if (context.messages && context.messages[0]) {
          context.messages[0].content += `\n${optimizationPrompt}`;
        }
      }
    }
  };
}
