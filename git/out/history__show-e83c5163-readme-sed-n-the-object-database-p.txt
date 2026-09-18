$ git show e83c5163:README | sed -n '/^The object database/,/^$/p'
The object database is literally just a content-addressable collection
of objects.  All objects are named by their content, which is
approximated by the SHA1 hash of the object itself.  Objects may refer
to other objects (by referencing their SHA1 hash), and so you can build
up a hierarchy of objects. 

