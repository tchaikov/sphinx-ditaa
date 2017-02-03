sphinx-ditaa
--------------------------------

This adds a basic ditaa builder for sphinx

## Installation
```shell
pip install sphinx-ditaa
```

install [ditaa command](http://ditaa.sourceforge.net/)

## Using the Ditaa with Sphinx

add `sphinx.ext.ditaa` to the `extensions` list in `conf.py`:

```python
extensions = [
   ... other extensions here ...
   sphinx.ext.ditaa
   ]

# ditaa command. should be install ditaa
ditaa = 'ditaa'  # ditaa command
# ditaa_args = ''  # custom ditaa args
```

write ditaa code in `rst` file.

```
    .. ditaa::
      +--------+   +-------+    +-------+
      |        | --+ ditaa +--> |       |
      |  Text  |   +-------+    |diagram|
      |Document|   |!magic!|    |       |
      |     {d}|   |       |    |       |
      +---+----+   +-------+    +-------+
          :                         ^
          |       Lots of work      |
          +-------------------------+
```
