import 'dart:async';
import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' show join;
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;

Future<void> main() async {
  // Ensure that plugin services are initialized
  WidgetsFlutterBinding.ensureInitialized();
  // Obtain a list of the available cameras on the device.
  final cameras = await availableCameras();
  // Get a specific camera from the list of available cameras.
  final firstCamera = cameras.first;

  runApp(StyleTransferApp(firstCamera));
}

class StyleTransferApp extends StatelessWidget {
  final CameraDescription _camera;

  StyleTransferApp(this._camera);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
        title: 'Style Transfer',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          visualDensity: VisualDensity.adaptivePlatformDensity,
        ),
        initialRoute: '/',
        routes: {
          '/': (context) => new HomePage(title: 'Style Transfer Flutter'),
          '/camera': (context) => new TakePictureScreen(camera: _camera),
        });
  }
}

class HomePage extends StatefulWidget {
  HomePage({Key key, this.title}) : super(key: key);

  final String title;

  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: Center(
        child: GridView.count(
            primary: false,
            padding: const EdgeInsets.all(20),
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            crossAxisCount: 2,
            children: <Widget>[
              for (var i = 0; i < 10; i += 1)
                Container(
                  child: GestureDetector(
                    onTap: () {
                      Navigator.pushNamed(context, '/camera',
                          arguments: 'assets/images/style$i.jpg');
                    },
                    child:
                        Image(image: AssetImage('assets/images/style$i.jpg')),
                  ),
                ),
            ]),
      ),
    );
  }
}

class TakePictureScreen extends StatefulWidget {
  final CameraDescription camera;

  const TakePictureScreen({Key key, @required this.camera}) : super(key: key);

  @override
  TakePictureScreenState createState() => TakePictureScreenState();
}

class TakePictureScreenState extends State<TakePictureScreen> {
  CameraController _controller;
  Future<void> _initializeControllerFuture;

  @override
  void initState() {
    super.initState();

    _controller = CameraController(
      widget.camera,
      ResolutionPreset.medium,
    );

    // Initialize the controller. This returns a Future.
    _initializeControllerFuture = _controller.initialize();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final String styleImg = ModalRoute.of(context).settings.arguments;

    return Scaffold(
      appBar: AppBar(title: Text('Take a picture')),
      body: FutureBuilder<void>(
        future: _initializeControllerFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.done) {
            // If the Future is complete, display the preview.
            return CameraPreview(_controller);
          } else {
            // Otherwise, display a loading indicator.
            return Center(child: CircularProgressIndicator());
          }
        },
      ),
      floatingActionButton: FloatingActionButton(
        child: Icon(Icons.camera_alt),
        // Provide an onPressed callback.
        onPressed: () async {
          // Take the Picture in a try / catch block.
          try {
            // Ensure that the camera is initialized.
            await _initializeControllerFuture;

            // Construct the path where the image should be saved using the
            // path package.
            final path = join(
              // Store the picture in the temp directory.
              // Find the temp directory using the `path_provider` plugin.
              (await getTemporaryDirectory()).path,
              '${DateTime.now()}.png',
            );
            // Attempt to take a picture and log where it's been saved.
            await _controller.takePicture(path);

            // If the picture was taken, display it on a new screen.
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => DisplayPastiche(
                  contentPath: path,
                  stylePath: styleImg,
                ),
              ),
            );
          } catch (e) {
            // If an error occurs, log the error to the console.
            print(e);
          }
        },
      ),
    );
  }
}

class DisplayPastiche extends StatefulWidget {
  final String contentPath;
  final String stylePath;

  const DisplayPastiche(
      {Key key, @required this.contentPath, @required this.stylePath})
      : super(key: key);

  @override
  _DisplayPasticheState createState() => _DisplayPasticheState();
}

class _DisplayPasticheState extends State<DisplayPastiche> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Pastiche')),
      body: Wrap(children: <Widget>[
        FractionallySizedBox(
          widthFactor: 0.5,
          child: Padding(
            padding: EdgeInsets.all(10),
            child: Image.file(
              File(widget.contentPath),
              width: 256,
              height: 256,
              fit: BoxFit.cover,
            ),
          ),
        ),
        FractionallySizedBox(
          widthFactor: 0.5,
          child: Padding(
            padding: EdgeInsets.all(10),
            child: Image.asset(
              widget.stylePath,
              width: 256,
              height: 256,
              fit: BoxFit.cover,
            ),
          ),
        ),
        Padding(
          padding: EdgeInsets.all(10),
          child: Center(
            child: FutureBuilder<String>(
              future: styleImage(widget.contentPath, widget.stylePath),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.done) {
                  return RotatedBox(
                    quarterTurns: 5,
                    child: Image.file(
                      File(snapshot.data),
                      width: 512,
                      height: 512,
                      fit: BoxFit.cover,
                    )
                  );
                } else {
                  return CircularProgressIndicator();
                }
              },
            )
          )
        ),
      ]),
    );
  }
}

Future<String> styleImage(String contentPath, String stylePath) async {
  var styledImgBytes = (await rootBundle.load(stylePath)).buffer.asUint8List();
  var uri = Uri.parse('http://192.168.2.11:8000/style');
  var request = http.MultipartRequest('POST', uri)
    ..files.add(await http.MultipartFile.fromPath('content_img', contentPath))
    ..files.add(http.MultipartFile.fromBytes('style_img', styledImgBytes,
        filename: 'style.jpg'));
  // http.StreamedResponse
  var response = await request.send();
  if (response.statusCode == 200) print('Uploaded!');

  var responseData = await response.stream.toBytes();
  String pastichePath = join(
    // Store the picture in the temp directory.
    // Find the temp directory using the `path_provider` plugin.
    (await getTemporaryDirectory()).path,
    '${DateTime.now()}.png',
  );
  File newFile = new File(pastichePath);
  await newFile.writeAsBytes(responseData);
  return pastichePath;
}
