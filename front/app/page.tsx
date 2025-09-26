"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileSpreadsheet, FileText, BarChart3, TrendingUp, Users, DollarSign, Leaf, Download } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import toast from "react-hot-toast"
import * as XLSX from 'xlsx'

interface PreviewData {
  type: "excel" | "pdf"
  content: any
  filename: string
}

export default function ReportesPage() {
  const [fincaName, setFincaName] = useState("")
  const [producto, setProducto] = useState("")
  const [isLoading, setIsLoading] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<Record<string, PreviewData>>({})
  const [backendStatus, setBackendStatus] = useState<string>("unknown")

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/health")
        console.log("Respuesta /api/health:", res)
        if (res.ok) {
          setBackendStatus("online")
        } else {
          setBackendStatus("offline")
        }
      } catch (err) {
        console.error("Error al conectar con backend:", err)
        setBackendStatus("offline")
      }
    }
    checkBackend()
  }, [])

  const handleGeneratePreview = async (
    reportId: string,
    endpoint: string,
    filename: string,
    fileType: "excel" | "pdf",
  ) => {
    setIsLoading(reportId)

    const loadingToast = toast.loading("Generando vista previa...")

    try {
      const response = await fetch(endpoint)

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("El endpoint del reporte no fue encontrado")
        } else if (response.status === 500) {
          throw new Error("Error interno del servidor al generar el reporte")
        } else if (response.status === 400) {
          throw new Error("Parámetros inválidos para generar el reporte")
        } else {
          throw new Error(`Error ${response.status}: ${response.statusText}`)
        }
      }

      const blob = await response.blob()

      if (blob.size === 0) {
        throw new Error("El reporte generado está vacío")
      }

      if (fileType === "pdf") {
        const pdfUrl = window.URL.createObjectURL(blob)
        setPreviewData((prev) => ({
          ...prev,
          [reportId]: {
            type: "pdf",
            content: pdfUrl,
            filename,
          },
        }))
      } else {
        const arrayBuffer = await blob.arrayBuffer()
        setPreviewData((prev) => ({
          ...prev,
          [reportId]: {
            type: "excel",
            content: arrayBuffer,
            filename,
          },
        }))
      }

      toast.success("Vista previa generada exitosamente", { id: loadingToast })
    } catch (error) {
      console.error("Error:", error)

      const errorMessage = error instanceof Error ? error.message : "Error desconocido al generar el reporte"
      toast.error(errorMessage, { id: loadingToast })
    } finally {
      setIsLoading(null)
    }
  }

  const handleDownload = async (endpoint: string, filename: string) => {
    const loadingToast = toast.loading("Descargando archivo...")

    try {
      const response = await fetch(endpoint)

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success("Archivo descargado exitosamente", { id: loadingToast })
    } catch (error) {
      console.error("Error:", error)
      const errorMessage = error instanceof Error ? error.message : "Error al descargar el archivo"
      toast.error(errorMessage, { id: loadingToast })
    }
  }

  const ExcelPreview = ({ arrayBuffer, filename }: { arrayBuffer: ArrayBuffer; filename: string }) => {
    const [excelData, setExcelData] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
      const loadExcel = async () => {
        try {
          // Procesar el ArrayBuffer del Excel usando XLSX
          const workbook = XLSX.read(arrayBuffer, { type: 'array' })
          const firstSheetName = workbook.SheetNames[0]
          const worksheet = workbook.Sheets[firstSheetName]
          
          // Convertir la hoja a array de arrays
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' })
          
          // Si no hay datos, mostrar estructura vacía
          if (jsonData.length === 0) {
            setExcelData({
              sheets: [firstSheetName],
              data: [
                ["Nombre Productor", "Área", "Producto", "Cantidad", "Costo"],
                ["Sin datos disponibles", "", "", "", ""]
              ],
            })
          } else {
            setExcelData({
              sheets: [firstSheetName],
              data: jsonData,
            })
          }
          
          setLoading(false)
        } catch (error) {
          console.error("Error loading Excel:", error)
          setLoading(false)
          toast.error("Error al procesar el archivo Excel")
          
          // Fallback con estructura esperada
          setExcelData({
            sheets: ["Datos"],
            data: [
              ["Nombre Productor", "Área", "Producto", "Cantidad", "Costo"],
              ["Error al cargar datos", "", "", "", ""]
            ],
          })
        }
      }
      loadExcel()
    }, [arrayBuffer])

    if (loading) {
      return (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          <span className="ml-2 text-sm">Cargando datos...</span>
        </div>
      )
    }

    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <FileSpreadsheet className="h-3 w-3" />
          {filename}
        </div>
        {excelData && (
          <div className="border rounded-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    {excelData.data[0]?.map((header: string, index: number) => (
                      <th key={index} className="px-3 py-2 text-left font-medium text-xs">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {excelData.data.slice(1).map((row: any[], rowIndex: number) => (
                    <tr key={rowIndex} className="border-t">
                      {row.map((cell: any, cellIndex: number) => (
                        <td key={cellIndex} className="px-3 py-2 text-xs">
                          {cell?.toString() || ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    )
  }

  const PDFPreview = ({ pdfUrl, filename }: { pdfUrl: string; filename: string }) => {
    const handlePDFError = () => {
      toast.error("Error al cargar la vista previa del PDF")
    }

    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <FileText className="h-3 w-3" />
          {filename}
        </div>
        <div className="border rounded-md overflow-hidden bg-muted/20">
          <iframe src={pdfUrl} className="w-full h-64" title="Vista previa del PDF" onError={handlePDFError} />
        </div>
      </div>
    )
  }

  const reportes = [
    {
      id: "global",
      title: "Reporte Global Consolidado",
      description: "Información consolidada de todos los productores y sus costos de producción",
      icon: <BarChart3 className="h-6 w-6" />,
      endpoint: "http://localhost:8000/reporte/reporteglobal",
      filename: "reporte_global.xlsx",
      type: "excel" as const,
      userType: "Administrador",
      requiresInput: false,
      color: "bg-primary/10 text-primary border-primary/20",
    },
    {
      id: "historico",
      title: "Histórico de Producción",
      description: "Gráfica del histórico de producción por finca para análisis temporal",
      icon: <TrendingUp className="h-6 w-6" />,
      endpoint: `http://localhost:8000/reporte/historico/pdf?nombre=${encodeURIComponent(fincaName)}`,
      filename: `historico_${fincaName.replace(/\s+/g, "_")}.pdf`,
      type: "pdf" as const,
      userType: "Productor",
      requiresInput: true,
      inputType: "finca",
      color: "bg-accent/10 text-accent border-accent/20",
    },
    {
      id: "top3",
      title: "Top 3 Productores",
      description: "Los 3 productores que más generan de un producto específico",
      icon: <Users className="h-6 w-6" />,
      endpoint: `http://localhost:8000/reporte/top3/top3?producto=${encodeURIComponent(producto)}`,
      filename: `top3_${producto.replace(/\s+/g, "_")}.xlsx`,
      type: "excel" as const,
      userType: "Administrador",
      requiresInput: true,
      inputType: "producto",
      color: "bg-chart-2/10 text-chart-2 border-chart-2/20",
    },
    {
      id: "costos",
      title: "Costos Agrupados",
      description: "Total de costos agrupados por productos para análisis financiero",
      icon: <DollarSign className="h-6 w-6" />,
      endpoint: `http://localhost:8000/reporte/costosagrupados/costos?nombre=${encodeURIComponent(fincaName)}`,
      filename: `costos_agrupados_${fincaName.replace(/\s+/g, "_")}.xlsx`,
      type: "excel" as const,
      userType: "Productor",
      requiresInput: true,
      inputType: "finca",
      color: "bg-chart-3/10 text-chart-3 border-chart-3/20",
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/10 mb-2 sm:mb-0">
              <Leaf className="h-8 w-8 text-primary" />
            </div>
            <div className="w-full">
              <h1 className="text-2xl md:text-3xl font-bold text-foreground break-words">EverGreen Analytics</h1>
              <p className="text-muted-foreground text-base md:text-lg leading-snug break-words">Sistema de análisis para la gestión agrícola inteligente</p>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 mt-2 w-full">
                <Badge variant="secondary" className="text-xs md:text-sm w-full sm:w-auto">
                  Módulo Analítica (ANA) - Implementado con TextX
                </Badge>
                <Badge
                  variant={backendStatus === "online" ? "default" : backendStatus === "offline" ? "destructive" : "secondary"}
                  className="text-xs md:text-sm w-full sm:w-auto"
                >
                  Backend: {backendStatus === "online" ? "Online" : backendStatus === "offline" ? "Offline" : "Desconocido"}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-2 sm:px-6 py-4 sm:py-8">
        {/* Hero Section */}
        <section className="mb-8 sm:mb-12 text-center">
          <div className="max-w-3xl mx-auto px-2">
            <h2 className="text-2xl sm:text-4xl font-bold text-balance mb-2 sm:mb-4">Reportes Inteligentes para el Futuro Agrícola</h2>
            <p className="text-base sm:text-xl text-muted-foreground text-pretty leading-relaxed">
              Accede a información consolidada sobre producción, costos y rendimiento. Toma decisiones informadas con
              datos precisos y actualizados.
            </p>
          </div>
        </section>

        {/* Input Section */}
        <section className="mb-6 sm:mb-8">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                <span className="text-base sm:text-lg">Parámetros de Consulta</span>
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">Completa los campos necesarios para generar los reportes específicos</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="finca" className="text-xs sm:text-sm">Nombre de la Finca</Label>
                  <Select value={fincaName} onValueChange={setFincaName}>
                    <SelectTrigger className="bg-background text-xs sm:text-sm">
                      <SelectValue placeholder="Selecciona una finca" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Finca 1">Finca 1</SelectItem>
                      <SelectItem value="Finca 2">Finca 2</SelectItem>
                      <SelectItem value="Finca 3">Finca 3</SelectItem>
                      <SelectItem value="Finca 4">Finca 4</SelectItem>
                      <SelectItem value="Finca 5">Finca 5</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs sm:text-sm text-muted-foreground">Requerido para reportes de histórico y costos</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="producto" className="text-xs sm:text-sm">Producto</Label>
                  <Select value={producto} onValueChange={setProducto}>
                    <SelectTrigger className="bg-background text-xs sm:text-sm">
                      <SelectValue placeholder="Selecciona un producto" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Café">Café</SelectItem>
                      <SelectItem value="Cacao">Cacao</SelectItem>
                      <SelectItem value="Maíz">Maíz</SelectItem>
                      <SelectItem value="Frijol">Frijol</SelectItem>
                      <SelectItem value="Plátano">Plátano</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs sm:text-sm text-muted-foreground">Requerido para reporte Top 3</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Reports Grid */}
        <section>
          <div className="mb-4 sm:mb-6">
            <h3 className="text-lg sm:text-2xl font-bold mb-1 sm:mb-2">Reportes Disponibles</h3>
            <p className="text-xs sm:text-sm text-muted-foreground">Selecciona el tipo de reporte que necesitas generar</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            {reportes.map((reporte) => {
              const canGenerate =
                !reporte.requiresInput ||
                (reporte.inputType === "finca" && fincaName.trim()) ||
                (reporte.inputType === "producto" && producto)

              const hasPreview = previewData[reporte.id]

              return (
                <Card key={reporte.id} className={`transition-all duration-200 hover:shadow-lg ${reporte.color}`}>
                  <CardHeader>
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-background/50">{reporte.icon}</div>
                        <div>
                          <CardTitle className="text-base sm:text-lg">{reporte.title}</CardTitle>
                          <Badge variant="secondary" className="mt-1 text-xs sm:text-sm">
                            {reporte.userType}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 text-xs sm:text-sm text-muted-foreground">
                        {reporte.type === "excel" ? (
                          <FileSpreadsheet className="h-4 w-4" />
                        ) : (
                          <FileText className="h-4 w-4" />
                        )}
                        {reporte.type.toUpperCase()}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs sm:text-sm text-muted-foreground mb-2 sm:mb-4 leading-relaxed">{reporte.description}</p>

                    {reporte.requiresInput && (
                      <div className="mb-2 sm:mb-4 p-2 sm:p-3 bg-muted/50 rounded-lg">
                        <p className="text-xs sm:text-sm text-muted-foreground">
                          <strong>Requiere:</strong>{" "}
                          {reporte.inputType === "finca" ? "Nombre de la finca" : "Selección de producto"}
                        </p>
                      </div>
                    )}

                    {hasPreview && (
                      <div className="mb-2 sm:mb-4 p-2 sm:p-4 bg-background/50 rounded-lg border">
                        <h4 className="text-xs sm:text-sm font-medium mb-2 sm:mb-3 text-foreground">Vista Previa:</h4>
                        {hasPreview.type === "excel" ? (
                          <ExcelPreview arrayBuffer={hasPreview.content} filename={hasPreview.filename} />
                        ) : (
                          <PDFPreview pdfUrl={hasPreview.content} filename={hasPreview.filename} />
                        )}
                      </div>
                    )}

                    <div className="space-y-2">
                      <Button
                        onClick={() =>
                          handleGeneratePreview(reporte.id, reporte.endpoint, reporte.filename, reporte.type)
                        }
                        disabled={!canGenerate || isLoading === reporte.id}
                        className="w-full"
                        variant={canGenerate ? "default" : "secondary"}
                      >
                        {isLoading === reporte.id ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
                            Generando vista previa...
                          </>
                        ) : (
                          <>
                            <FileText className="h-4 w-4 mr-2" />
                            {hasPreview ? "Actualizar Vista Previa" : "Generar Vista Previa"}
                          </>
                        )}
                      </Button>

                      {hasPreview && (
                        <Button
                          onClick={() => handleDownload(reporte.endpoint, reporte.filename)}
                          className="w-full"
                          variant="outline"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Descargar Archivo
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </section>

        {/* Footer Info */}
        <section className="mt-8 sm:mt-12 text-center">
          <Card className="max-w-4xl mx-auto bg-muted/30">
            <CardContent className="pt-4 sm:pt-6">
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 sm:gap-6 text-center">
                <div>
                  <div className="text-lg sm:text-2xl font-bold text-primary">4</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">Tipos de Reportes</div>
                </div>
                <div>
                  <div className="text-lg sm:text-2xl font-bold text-accent">Excel + PDF</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">Formatos Disponibles</div>
                </div>
                <div>
                  <div className="text-lg sm:text-2xl font-bold text-chart-2">Tiempo Real</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">Datos Actualizados</div>
                </div>
                <div>
                  <div className="text-lg sm:text-2xl font-bold text-chart-3">Seguro</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">Información Protegida</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>

      {/* Eliminar el Dialog */}
    </div>
  )
}

