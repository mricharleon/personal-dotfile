export default async function ContextPrunerPlugin() {
  const MAX_CHARACTERS = 8000; // Límite aproximado para evitar outputs masivos

  return {
    name: "context-pruner",
    hooks: {
      "tool.execute.after": async (context) => {
        const { result } = context;

        if (result && typeof result.content === "string" && result.content.length > MAX_CHARACTERS) {
          const originalLength = result.content.length;
          
          // Recortamos el contenido y añadimos una nota para el modelo
          result.content = result.content.substring(0, MAX_CHARACTERS) + 
            `\n\n[... Output recortado por el plugin ContextPruner. Se omitieron ${originalLength - MAX_CHARACTERS} caracteres para optimizar contexto ...]`;
          
          console.log(`[ContextPruner] Output recortado de ${originalLength} a ${MAX_CHARACTERS} caracteres.`);
        }
      }
    }
  };
}
