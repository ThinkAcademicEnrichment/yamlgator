# yamlgator

`yamlgator` is a powerful YAML preprocessor and macro engine designed to make your configuration files dynamic and manageable. It transforms simple, templated YAML files into fully resolved, complex configurations by handling variables, conditionals, file imports, Python code execution, and more, turning your static YAML into a powerful programming environment.

## Installation

Install `yamlgator` directly from PyPI:

```bash
pip install yamlgator
```

## Core Concept and Basic Usage

The workflow is straightforward:

1.  Create a YAML file using `yamlgator`'s special `)) ` syntax for dynamic transformations.
2.  Load your root YAML file using `YAMLator.load()`. This parses the file and prepares it for transformation.
3.  Call the `.transform()` method on the loaded object to process all macros and directives.
4.  Use the resulting `Tree` object, which can be dumped back to a standard YAML string or accessed directly.

Here is a "Hello, World" example:

```python
from yamlgator import YAMLator

# 1. A YAML string with a variable placeholder
yaml_string = """
name: world
message: Hello ))name!
"""

# 2. Load the YAML
yator = YAMLator.load(yaml_string)

# 3. Transform it
resolved_tree = yator.transform()

# 4. Use the result
print(resolved_tree)
```

**Output:**

```yaml
name: world
message: Hello world!

```

---

## Transformations Reference

`yamlgator`'s power comes from its various transformation directives. All directives start with `))`.

### Value Substitution (`transform_values`)

#### Simple Values
Substitutes placeholders with values defined elsewhere in the tree. Use `))key` for simple lookups or `)){path/to/key}` for full keychain lookups.

**Input:**

```yaml
server:
  host: 127.0.0.1
  port: 8080
app:
  api_url: http://)){server/host}:)){server/port}/api
  greeting: Welcome, ))user!
  # String values can be sliced
  mask: )){server/host}[:3].x.x.x
user: Alice
```

**Output:**

```yaml
server:
  host: 127.0.0.1
  port: 8080
app:
  api_url: http://127.0.0.1:8080/api
  greeting: Welcome, Alice!
  mask: 127.x.x.x
user: Alice
```

#### Path Values
Because of the `keychain` single key syntax (e.g. `))name` above) to lookup strings, path type values must be handled in a particular way, either by escaping a path seperator or using braces. This same type of escaping must be done for `-` characters as well.

**Input:**

```yaml
project-name: my-project
work-dir: /mnt/work
tmpfs-dir:
  )){work-dir}/tmpfs
tmpfs-2-dir:
  ))work-dir//tmpfs
tmp-dir:
  )){tmpfs-dir}/))project-name
tmp-2-dir:
  ))tmpfs-dir//))project-name
log-dir:
  )){tmpfs-dir}/logs
log-2-dir:
  ))tmpfs-dir//logs
```

**Output:**

```yaml
project-name: my-project
work-dir: /mnt/work
tmpfs-dir:
  /mnt/work/tmpfs
tmpfs-2-dir:
  /mnt/work/tmpfs
tmp-dir:
  /mnt/work/tmpfs/my-project
tmp-2-dir:
  /mnt/work/tmpfs/my-project
log-dir:
  /mnt/work/tmpfs/logs
log-2-dir:
  /mnt/work/tmpfs/logs
```

### Key Substitution (`transform_keys`)

Uses a variable to define the name of a key itself, allowing for dynamic structures.

**Input:**

```yaml
a-key:
  A_VALUE
)){a-key}-key:
  A_VALUE_2
)){A_VALUE-key}-key:
  A_VALUE_3
b-key:
  c-key:
    C_VALUE
)){b-key/c-key}-key:
  C_VALUE_2
key-d:
  key-e:
    ))a-key:
      A Deep Value
key-f:
  key-g:
    ))c-key:
      A Deeper Value
key-h:
  key-i:
    )){b-key/c-key}:
      A Deeper Value by keychain
key-j:
  ))a-key:
    key-x:
      X
    key-y:
      Y
```

**Output:**

```yaml
a-key:
  A_VALUE
A_VALUE-key:
  A_VALUE_2
A_VALUE_2-key:
  A_VALUE_3

b-key:
  c-key:
    C_VALUE
C_VALUE-key:
  C_VALUE_2
C_VALUE_2-holds-a-dict:
  dict-key-1:
    DICT_VAL_1
  dict-key-2:
    DICt_VAL_2
key-d:
  key-e:
    A_VALUE:
      A Deep Value
key-f:
  key-g:
    C_VALUE:
      A Deeper Value
key-h:
  key-i:
    C_VALUE:
      A Deeper Value by keychain
key-j:
  A_VALUE:
    key-x:
      X
    key-y:
      Y

```

### Positional Variables (`transform_ats`)

Accesses values relative to the current node's position. `))@` refers to the value of a sibling key within the same block, and `))@[-1]` refers to the parent block, enabling powerful relative lookups.

**Input:**

```yaml
config:
  a-key:
    ))@
  b-key:
    B_VALUE
  c-key:
    ))b-key
  d-key:
    The full name of this key is )){@}
  e-key:
    f-key:
      The short name of this key is ))@
    g-key: |
      This key is called both ))@ and )){@} depending
      on how the at variable is used.
  h-key:
    l-key: |
      this key's parent is ))@[-1] and it must work
      in multiline mode.
    m-key:
      this key's parent's parent is ))@[-2]
  g-key:
    i-key:
      the full name of this key's parent is )){@[-1]}
    j-key:
      k-key: |
        the full name of this key's parent's parent is )){@[-2]}
        and it must work in multiline mode.
    n-key:
      - this key is the ))@ key
      - this key's parent is the ))@[-1] key
      - this key's parent's parent is the ))@[-2] key
      - this key has a dash after it ))@[-1]-
  linux:
    version: 6.4.12
    vVx: v6.x
    ext: xz
    fetch-urls:
      - https://cdn.kernel.org/pub/))@[-1]/kernel/)){))@[-1]/vVx}/))@[-1]-)){))@[-1]/version}.tar.)){))@[-1]/ext}
  # This can be a useful idiom for complex configurations when a value is undefined; the trailing slash here is required
  project-type:
    ))))@/
```

**Output:**

```yaml
config:
  a-key:
    a-key
  b-key:
    B_VALUE
  c-key:
    B_VALUE
  d-key:
    The full name of this key is config/d-key
  e-key:
    f-key:
      The short name of this key is f-key
    g-key: |
      This key is called both g-key and config/e-key/g-key depending
      on how the at variable is used.
  h-key:
    l-key: |
      this key's parent is h-key and it must work
      in multiline mode.
    m-key:
      this key's parent's parent is config
  g-key:
    i-key:
      the full name of this key's parent is config/g-key
    j-key:
      k-key: |
        the full name of this key's parent's parent is config/g-key
        and it must work in multiline mode.
    n-key:
      - this key is the n-key key
      - this key's parent is the g-key key
      - this key's parent's parent is the config key
      - this key has a dash after it g-key-
  linux:
    version: 6.4.12
    vVx: v6.x
    ext: xz
    fetch-urls:
      - https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.4.12.tar.xz
    project-type:
        ))project-type/ 
```

### Conditional Values (`transform_ifs`)

Sets a value based on a condition, using a ternary-like syntax: `))?{condition: value_if_true: value_if_false}`. The `&`, `|` and `!` operators are supported. Unquoted strings are treated as keychains, quoted strings are treaded as such. Notice how cases are written, with no space between the `:` and the case expression.

**Input:**

```yaml

settings:
  debug_mode: true
  log_level: ))?{debug_mode :DEBUG :INFO}
# Note the ))@ use to specify the settings-2/debug_mode key
# Otherwise settings/debug_mode is selected by the depth-first rule for ambiguous keys
settings-2:
  debug_mode: n
  log_level: ))?{ ! ))@[-1]/debug_mode :INFO :DEBUG}

a:
  f: A
  g: hello
b: B
c: |
  some multiline
  text
d: False
e: ))?{ b == a/f & 'hello' == a/g :c :'I am False' }
# You can use an empty case for the false condition; returns an empty string
f: ))?{ b != a/f & 'hello' == a/g :'I am True' }
g: ))?{ b == a/f & 'hello' == a/g :'I am True' }
h: ))?{ b  !=  a/f  &  'hello'  ==  a/g  :'I am True'  :'I am False'  }
i: ))?{ b == a/f | 'hello' == a/g :c :d }

```

**Output:**

```yaml
settings:
  debug_mode: true
  log_level: DEBUG
settings-2:
  debug_mode: n
  log_level: INFO
a:
  f: A
  g: hello
b: B
c: |
  some multiline
  text
d: False
e: I am False
f: I am True
g: ''
h: I am True
i: |
  some multiline
  text
  
```

### Conditional Keys (`transform_if_keys`)

Includes or excludes an entire block of YAML based on a condition. The key of the block itself becomes the condition.

**Input:**

```yaml
is-a: y
some-data: hello
more-data: goodbye
# A trailing slash trims the root key of the case
))?{is-a}/:
  yes:
    my-yes-data: yes
  no:
    my-no-data: no
# No trailing slash preserves the root key of the case
))?{!is-a}:
  yes:
    my-yes-data: yes
  no:
    my-no-data: no
even-more-data: hohum
a-string:
  hello
# Slicing is permitted in comparisons 
))?{a-string[:-1] == 'hell'}/:
  yes:
    correct:
      1
  no:
    incorrect:
      0
enable_monitoring: false
# This entire block will be removed from the output
))?{enable_monitoring}:
  monitoring:
    endpoint: http://monitor.svc.cluster.local
    port: 9090
```

**Output:**

```yaml
is-a: y
some-data: hello
more-data: goodbye
my-yes-data: yes
no:
  my-no-data: no
even-more-data: hohum
a-string:
  hello
correct:
  1
enable_monitoring: false
```

### File Merging (`transform_imports`)

Merges the contents of an external YAML file into the current tree. The `))+` directive is followed by the key to merge into and the path to the file.

**`data/tree-data.yaml`:**

```yaml
u:
  v: V
  w: W
x:
  y: Y
  z: Z

uu:
  vv: ./more-tree-data.yaml#uu/vv/
  ww: ./more-tree-data.yaml#uu/vv/
```

**`data/more-tree-data.yaml`:**

```yaml
uu:
  vv: VV
  ww: WW
```

**Input:**

```yaml
config:
  # Paths are relative to the current file and must use the './' syntax
  ))+some-data:
    ./data/tree-data.yaml#uu
  ))+some-more-data:
    ./data/more-tree-data.yaml#uu/
```

**Output:**

```yaml
config:
  uu:
    vv: VV
    ww: WW
  vv: VV
  ww: WW
```

### YAML Embedding (`transform_yaml`)

Embeds an entire external YAML file as a structured value under a key, using `./data/tree-data.yaml` and `./data/more-tree-data.yaml` as defined above. Note the optional use of a `yaml` list to sequence a set of embeddings under a single key.

**Input:**

```yaml
my-choice: uu
a:
  - ./data/tree-data.yaml#u
  - ./data/tree-data.yaml#))my-choice

```

**Output:**

```yaml
a:
  u:
    v: V
    w: W
  uu:
    vv: VV
    ww: VV
```

### Plain Text Embedding (`transform_plaintext`)

Embeds the raw content of any file as a multiline string. This is perfect for including scripts, queries, or documents. Just append a `#` to the filename.

**`./data/plaintext.txt`:**

```bash
Here is some plain text.

# its structure should be preserved as a multi-line value under a key in a YAML file
))a-key = 1000


/dev/nvme0n1p1          /boot           vfat            noauto,noatime  1 2
```

**Input:**

```yaml
config:
  a-key: A_VALUE
  some-plaintext-data:
    ./data/a-plain-file#
```

**Output:**

```yaml
config:
  a-key: A_VALUE
  some-plaintext-data: |
    Here is some plain text.

    # its structure should be preserved as a multi-line value under a key in a YAML file
    A_VALUE = 1000


    /dev/nvme0n1p1          /boot           vfat            noauto,noatime  1 2
```

### Python Execution (`transform_bangs`)
Its is possible to subclass `YAMLator` to create custom transformers inline.

```python
from YAMLgator import YAMLator

class BangYAMLator(YAMLator):
    def short_uuid(self):
        import uuid
        return str(uuid.uuid1())[:4]

    def uuid(self):
        import uuid
        return str(uuid.uuid1())

    def token_hex(self, n):
        import secrets
        return str(secrets.token_hex(n))

    def date(self, date_fmt_str):
        import datetime
        return datetime.datetime.now().strftime(date_fmt_str)

    def replace(self, s, char1, char2):
        return str(s).replace(char1, char2)
    
yaml_string = """
short-id: ))!short_uuid()
long-id: ))!uuid()
token: ))!token_hex(16)
now: ))!date('%Y-%m-%dT%H:%M:%S.%f')
a-key: xxx-xxx
substring-to-replace: 'x-x'
replacement-substring: y_y
# Notice the two forms of escaping the '-' character, similar to '/' escaping
# string arguments to ))! functions must be quoted
replace-))substring-to-replace/-with-)){replacement-substring}-in-))a-key: ))!replace('))a-key','))substring-to-replace','))replacement-substring')
"""

# 2. Load the YAML
bangyator = BangYAMLator.load(yaml_string)

# 3. Transform it
resolved_tree = bangyator.transform()

# 4. Use the result
print(resolved_tree)

```

**Output (example):**

```yaml
short-id: 08de
long-id: 08de36da-8da6-11f0-bf3d-107b444d8de9
token: 286488924293f9a8339917f4195c02b1
now: '2025-09-09T13:54:30.137823'
a-key: xxx-xxx
substring-to-replace: x-x
replacement-substring: y_y
replace-x-x-with-y_y-in-xxx-xxx: xxy_yxx
```

## Validation

Before you run a potentially complex transformation, you can perform a "pre-flight" check using the `.validate()` method. It scans the `YAMLator` object for issues like circular dependencies, undefined variables, and invalid syntax, creating a record of the issue.

```python
from yamlgator import YAMLator

yaml_string="""
service-a:
  # The endpoint for service-a depends on the location of service-b
  endpoint: https://api.example.com/)){service-b/path}

service-b:
  # The path for service-b is built using the asset location from service-c
  path: v2/data/)){service-c/assets}

service-c:
  # The asset location for service-c incorrectly points back to service-a's endpoint
  assets: static/)){service-a/endpoint}
  # a common idiom
service-d:
  widgets: ))service-d

service-e:
  garbage: )){config/unknown-stuff}

service-f:
  value: SERVICE_F
service-g:
  bad-token: ))service-ff//THINGS
"""
yator = YAMLator.load(yaml_string)

all_issues = yator.validate()
for issue in all_issues:
    print(f"\t{issue}")
```

**Output:**
```terminaloutput
    Circular dependency found: service-b/path -> service-c/assets -> service-a/endpoint
    Warning: Undefined variable ')){config/unknown-stuff}' is found.
```

## Hidden Keys

Appending any key name with an underscore hides it from the transformation engine while allowing its value to be accessed via the `))` syntax.

**Input**
```yaml
a: A
_project-name-template: ))@-project
super-project-name: )){_project-name-template}
```

**Output**
```yaml
a: A
_project-name-template: ))@-project
super-project-name: super-project-name-project
```

## Advanced Usage: Automatic Type Conversion

`yamlgator` can automatically convert string values from your YAML file into rich Python objects like `pathlib.Path`, `yarl.URL`, or `bool` when you use the `set_config_attrs()` method.

This works by convention. When you create a subclass of `YAMLator`, you can define uppercase attributes on it. When you call `set_config_attrs()`, `yamlgator` maps the keys from your YAML file to these attributes. If a YAML key matches a specific naming pattern, its value is automatically cast to the corresponding Python type.

Here are the key naming conventions:

| Key Pattern | Description | Converted Type |
| :--- | :--- | :--- |
| `is-` or `use-` (prefix) | For boolean flags (e.g., `is-enabled`). | `bool` |
| `-path` or `-dir` (suffix) | For file system paths (e.g., `output-dir`). | `pathlib.Path` |
| `-url` (suffix) | For URLs (e.g., `api-url`). | `yarl.URL` |

#### Complete Example

Here’s how to put it all together.

**1. Python Subclass (`my_config.py`)**

```python
import pathlib
from yarl import URL
from yamlgator import YAMLator

class MyConfig(YAMLator):
    WORK_DIR = None
    IS_PRODUCTION = None
    API_URL = None
```

**2. YAML Configuration (`config.yaml`)**

```yaml
config:
  work-dir: /tmp/data
  is-production: y
  api-url: https://api.example.com
```

**3. Loading and Verifying**

```python
import pathlib
from yarl import URL
# Assuming my_config.py and config.yaml are in the same directory
from my_config import MyConfig

# Load the YAML file
config = MyConfig.load("config.yaml")

# Transform and set attributes
config.transform()
config.set_config_attrs()

# Verify the types
print(f"WORK_DIR: {config.WORK_DIR} (type: {type(config.WORK_DIR)})")
print(f"IS_PRODUCTION: {config.IS_PRODUCTION} (type: {type(config.IS_PRODUCTION)})")
print(f"API_URL: {config.API_URL} (type: {type(config.API_URL)})")

assert isinstance(config.WORK_DIR, pathlib.Path)
assert isinstance(config.IS_PRODUCTION, bool)
assert config.IS_PRODUCTION is True
assert isinstance(config.API_URL, URL)
```
