export default async function EnvProtectionPlugin() {
  return {
    name: "env-protection",
    hooks: {
      "tool.execute.before": async (context) => {
        const { toolName, args } = context;
        
        // Monitoreamos herramientas comunes de lectura de archivos
        if (toolName === "view_file" || toolName === "read_file" || toolName === "filesystem__read") {
          const filePath = (args.path || args.filePath || "").toLowerCase();
          
          // Bloqueamos archivos .env, configuraciones de producción o llaves privadas
          if (
            filePath.includes(".env") || 
            filePath.includes("id_rsa") || 
            filePath.includes("credentials.json")
          ) {
            throw new Error(
              "Acceso denegado por política de seguridad: No tienes permitido leer archivos de configuración de credenciales directas (.env, llaves, etc.). Pídele al usuario los valores específicos si los necesitas."
            );
          }
        }
      }
    }
  };
}
