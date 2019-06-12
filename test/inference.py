import ai_integration
import tensorflow as tf


# TODO ensure model loads only once
# TODO no temp files

def initialize_model():
    with tf.Graph().as_default():
        init = tf.global_variables_initializer()
        config = tf.ConfigProto()
        with tf.gfile.GFile("test/4pp_eusr_pirm.pb", 'rb') as f:
            model_graph_def = tf.GraphDef()
            model_graph_def.ParseFromString(f.read())

        config.gpu_options.per_process_gpu_memory_fraction = 0.12
        sess = tf.Session(config=config)
        sess.run(init)

        input_image_placeholder = tf.placeholder(tf.float32, name='input_image_placeholder')

        print('Initialized model')
        while True:
            with ai_integration.get_next_input(inputs_schema={
                "image": {
                    "type": "image"
                }
            }) as inputs_dict:
                input_image = inputs_dict["image"]
                input_image = [tf.image.decode_image(input_image, dtype=tf.uint8, channels=3)]
                input_image = tf.cast(input_image, tf.float32)

                model_output = tf.import_graph_def(model_graph_def, name='model', input_map={'sr_input:0': input_image_placeholder},
                                                   return_elements=['sr_output:0'])[0]
                model_output = model_output[0, :, :, :]
                model_output = tf.round(model_output)
                model_output = tf.clip_by_value(model_output, 0, 255)
                model_output = tf.cast(model_output, tf.uint8)
                image = tf.image.encode_jpeg(model_output, chroma_downsampling=False)
                result_data = {"content-type": 'text/plain',
                               "data": None,
                               "success": False,
                               "error": None}

                run_output = sess.run([image], feed_dict={'input_image_placeholder:0': input_image})
                png_bytes = run_output[0]
                output_img_bytes = png_bytes
                print('Done')
                result_data["data"] = output_img_bytes
                result_data["content-type"] = 'image/jpeg'
                result_data["success"] = True
                result_data["error"] = None
                print('Finished inference')
                ai_integration.send_result(result_data)
