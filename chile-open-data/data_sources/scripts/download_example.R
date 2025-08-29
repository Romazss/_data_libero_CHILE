# Script de descarga de ejemplo - Fase 1
# Biblioteca de Datos Abiertos de Chile
# 
# Este script demuestra cómo descargar datasets usando la configuración
# definida en sources.yaml desde R.

# Cargar librerías necesarias
if (!require(yaml)) install.packages("yaml")
if (!require(httr)) install.packages("httr")
if (!require(jsonlite)) install.packages("jsonlite")

library(yaml)
library(httr)
library(jsonlite)

# Función para cargar configuración de fuentes
load_sources <- function(sources_path = "data_sources/config/sources.yaml") {
  if (!file.exists(sources_path)) {
    stop(paste("No se encontró", sources_path))
  }
  
  data <- read_yaml(sources_path)
  
  # Soporta tanto 'datasets' como 'sources'
  datasets <- data$datasets
  if (is.null(datasets)) {
    datasets <- data$sources
  }
  
  if (is.null(datasets) || length(datasets) == 0) {
    stop("No se encontraron datasets en la configuración")
  }
  
  return(datasets)
}

# Función para verificar disponibilidad de un dataset
check_dataset_availability <- function(dataset) {
  url <- dataset$url
  method <- ifelse(is.null(dataset$method), "HEAD", toupper(dataset$method))
  timeout_val <- ifelse(is.null(dataset$timeout), 10, as.numeric(dataset$timeout))
  
  tryCatch({
    if (method == "HEAD") {
      response <- HEAD(url, timeout(timeout_val))
    } else {
      response <- GET(url, timeout(timeout_val))
    }
    
    list(
      id = dataset$id,
      name = dataset$name,
      url = url,
      status = ifelse(status_code(response) < 400, "available", "unavailable"),
      status_code = status_code(response),
      category = dataset$category
    )
  }, error = function(e) {
    list(
      id = dataset$id,
      name = dataset$name,
      url = url,
      status = "error",
      error = as.character(e),
      category = dataset$category
    )
  })
}

# Función para descargar un dataset (simulado)
download_dataset <- function(dataset, output_dir = "downloads", dry_run = FALSE) {
  # Crear directorio de salida
  dataset_dir <- file.path(output_dir, dataset$category, dataset$id)
  if (!dir.exists(dataset_dir)) {
    dir.create(dataset_dir, recursive = TRUE)
  }
  
  if (dry_run) {
    cat(sprintf("[DRY-RUN] Descargaría: %s -> %s\n", dataset$name, dataset_dir))
    return(TRUE)
  }
  
  # En una implementación real, aquí iría la lógica de descarga específica
  cat(sprintf("⚠️  Descarga simulada: %s\n", dataset$name))
  cat(sprintf("   URL: %s\n", dataset$url))
  cat(sprintf("   Categoría: %s\n", dataset$category))
  
  # Crear un archivo de ejemplo
  metadata_file <- file.path(dataset_dir, paste0(dataset$id, "_metadata.txt"))
  metadata_content <- paste(
    sprintf("Dataset: %s", dataset$name),
    sprintf("URL: %s", dataset$url),
    sprintf("Categoría: %s", dataset$category),
    sprintf("Descripción: %s", ifelse(is.null(dataset$description), "Sin descripción", dataset$description)),
    sep = "\n"
  )
  
  writeLines(metadata_content, metadata_file)
  cat(sprintf("   Metadata guardada en: %s\n", metadata_file))
  
  return(TRUE)
}

# Función principal de descarga
download_chile_data <- function(sources_path = "data_sources/config/sources.yaml",
                               output_dir = "downloads",
                               dataset_id = NULL,
                               category = NULL,
                               check_only = FALSE,
                               dry_run = FALSE) {
  
  tryCatch({
    # Cargar configuración
    datasets <- load_sources(sources_path)
    cat(sprintf("📂 Cargados %d datasets desde %s\n", length(datasets), sources_path))
    
    # Filtrar por dataset específico
    if (!is.null(dataset_id)) {
      datasets <- datasets[sapply(datasets, function(ds) ds$id == dataset_id)]
      if (length(datasets) == 0) {
        stop(sprintf("Dataset '%s' no encontrado", dataset_id))
      }
    }
    
    # Filtrar por categoría
    if (!is.null(category)) {
      datasets <- datasets[sapply(datasets, function(ds) ds$category == category)]
      if (length(datasets) == 0) {
        stop(sprintf("No se encontraron datasets en la categoría '%s'", category))
      }
    }
    
    # Verificar disponibilidad
    cat("\n🔍 Verificando disponibilidad de datasets...\n")
    results <- lapply(datasets, check_dataset_availability)
    
    for (result in results) {
      status_emoji <- ifelse(result$status == "available", "✅", "❌")
      cat(sprintf("%s %s (%s) - %s\n", status_emoji, result$name, result$category, result$status))
    }
    
    if (check_only) {
      available_count <- sum(sapply(results, function(r) r$status == "available"))
      cat(sprintf("\n📊 Resumen: %d disponibles de %d\n", available_count, length(results)))
      return(invisible(results))
    }
    
    # Descargar datasets disponibles
    available_indices <- which(sapply(results, function(r) r$status == "available"))
    available_datasets <- datasets[available_indices]
    
    if (length(available_datasets) == 0) {
      cat("\n❌ No hay datasets disponibles para descargar\n")
      return(invisible(results))
    }
    
    cat(sprintf("\n⬇️  Descargando %d datasets...\n", length(available_datasets)))
    success_count <- 0
    
    for (dataset in available_datasets) {
      if (download_dataset(dataset, output_dir, dry_run)) {
        success_count <- success_count + 1
      }
    }
    
    cat(sprintf("\n✅ Proceso completado: %d/%d datasets procesados\n", 
                success_count, length(available_datasets)))
    
    return(invisible(results))
    
  }, error = function(e) {
    cat(sprintf("❌ Error: %s\n", as.character(e)))
    stop(e)
  })
}

# Ejemplos de uso:

# Verificar disponibilidad de todos los datasets
# download_chile_data(check_only = TRUE)

# Descargar todos los datasets disponibles (simulado)
# download_chile_data(dry_run = TRUE)

# Descargar solo datasets de economía
# download_chile_data(category = "economía", dry_run = TRUE)

# Descargar un dataset específico
# download_chile_data(dataset_id = "bcentral_pib", dry_run = TRUE)

# Función auxiliar para mostrar ayuda
show_help <- function() {
  cat("📖 Biblioteca de Datos Abiertos de Chile - Script R\n\n")
  cat("Funciones disponibles:\n")
  cat("• download_chile_data(): Función principal de descarga\n")
  cat("• load_sources(): Cargar configuración desde YAML\n")
  cat("• check_dataset_availability(): Verificar un dataset\n\n")
  cat("Parámetros principales:\n")
  cat("• sources_path: Ruta al archivo sources.yaml\n")
  cat("• output_dir: Directorio de descarga\n")
  cat("• dataset_id: ID específico de dataset\n")
  cat("• category: Filtrar por categoría\n")
  cat("• check_only: Solo verificar disponibilidad\n")
  cat("• dry_run: Simular descarga\n\n")
  cat("Ejemplos:\n")
  cat("download_chile_data(check_only = TRUE)\n")
  cat("download_chile_data(category = 'economía', dry_run = TRUE)\n")
}

# Mostrar ayuda al cargar el script
cat("✅ Script de descarga R cargado correctamente.\n")
cat("💡 Usa show_help() para ver ejemplos de uso.\n")
