# Templates

<!-- badge:product Neon -->
<!-- badge:version +1.3.0 -->
<!-- badge:companion +2.8.25 -->

You can access the response data entered into the [template questionnaire](https://docs.pupil-labs.com/neon/data-collection/templates/#templates) on the phone and also set those responses remotely.
If the template is [properly configured](https://docs.pupil-labs.com/neon/data-collection/templates/#naming-scheme-for-recordings), this allows you to also define the recording name.

### Get Template Definition

Using the [`device.get_template`][pupil_labs.realtime_api.simple.Device.get_template] method, you can receive the definition of the template containing all questions and sections.

```py linenums="0"
--8<-- "examples/simple/templates.py:19:19"
```

??? quote "Template"

    ::: pupil_labs.realtime_api.models.Template

### Get Template Data

Using the [`device.get_template_data`][pupil_labs.realtime_api.simple.Device.get_template_data] method, you can receive the responses currently saved in the template.

```py linenums="0"
--8<-- "examples/simple/templates.py:22:22"
```

### Set Template Data

And using the [`device.post_template_data`][pupil_labs.realtime_api.simple.Device.post_template_data] method, you can set the template responses remotely.

```py linenums="0"
--8<-- "examples/simple/templates.py:112:112"
```

### Get Template Questions & Validate them

You can also retrieve individual questions by their ID using the [`template.get_question_by_id`][pupil_labs.realtime_api.models.Template.get_question_by_id] method and check the validity of a response using the [`template.validate_answer`](../../../api/async/#pupil_labs.realtime_api.models.TemplateItem.validate_answer) method.

## See it in action

<div class="video-container" style="margin: 20px auto; text-align: center;">
<iframe width="800" height="400" src="https://www.youtube-nocookie.com/embed/EblgXjsCMN4?si=qnEFEnPkHlIp6z7X" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

??? example "Check the whole example code here"

    ```py title="templates.py" linenums="1"
    --8<-- "examples/simple/templates.py"
    ```
