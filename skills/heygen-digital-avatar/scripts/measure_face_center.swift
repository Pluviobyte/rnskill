import AppKit
import Foundation
import Vision

struct FaceMeasure: Codable {
    let file: String
    let imageWidth: Int
    let imageHeight: Int
    let faceX: Double
    let faceY: Double
    let faceWidth: Double
    let faceHeight: Double
    let centerX: Double
    let centerY: Double
}

for path in CommandLine.arguments.dropFirst() {
    let url = URL(fileURLWithPath: path)
    guard let image = NSImage(contentsOf: url),
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        fputs("Unable to load \(path)\n", stderr)
        continue
    }

    let request = VNDetectFaceRectanglesRequest()
    let handler = VNImageRequestHandler(cgImage: cgImage, orientation: .up)
    try handler.perform([request])
    guard let face = request.results?.max(by: { $0.boundingBox.width < $1.boundingBox.width }) else {
        fputs("No face in \(path)\n", stderr)
        continue
    }

    let box = face.boundingBox
    let width = Double(cgImage.width)
    let height = Double(cgImage.height)
    let x = box.minX * width
    let y = (1.0 - box.maxY) * height
    let w = box.width * width
    let h = box.height * height
    let measure = FaceMeasure(
        file: url.lastPathComponent,
        imageWidth: cgImage.width,
        imageHeight: cgImage.height,
        faceX: x,
        faceY: y,
        faceWidth: w,
        faceHeight: h,
        centerX: x + w / 2.0,
        centerY: y + h / 2.0
    )
    let data = try JSONEncoder().encode(measure)
    print(String(data: data, encoding: .utf8)!)
}
