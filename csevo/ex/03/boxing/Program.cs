// 슬라이드 p3-v2-generics-box — 박싱: ArrayList 와 List<int>, C# 2.0
using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;

class App
{
    static void Store(Type t)
    {
        BindingFlags f = BindingFlags.NonPublic | BindingFlags.Instance;
        FieldInfo items = t.GetField("_items", f);
        Console.WriteLine(t.Name + " keeps " + items.FieldType);
    }

    static void Main()
    {
        Store(typeof(ArrayList));
        Store(typeof(List<int>));

        ArrayList a = new ArrayList();
        a.Add(42);                        // boxed once, here
        Console.WriteLine(object.ReferenceEquals(a[0], a[0]));

        List<int> b = new List<int>();
        b.Add(42);                        // stored as a plain int
        object x = b[0];                  // boxed here...
        object y = b[0];                  // ...and again here
        Console.WriteLine(object.ReferenceEquals(x, y));
    }
}
