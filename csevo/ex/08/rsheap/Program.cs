// 슬라이드 p8-v7_2-refstruct-heap — 힙에 두려 하면, C# 7.2
using System;
using System.Collections.Generic;

ref struct R { }

class App
{
    static void Main()
    {
        R r = new R();
        object o = r;                      // boxing
        ValueType v = r;                   // boxing again
        R[] arr = null;                    // an array element
        List<R> list = null;               // a type argument
        var t = (r, 1);                    // a tuple element
        string s = r.ToString();           // object's method
        Func<string> f = r.ToString;       // a method group
    }
}
