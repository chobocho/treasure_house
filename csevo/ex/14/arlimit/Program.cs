// 슬라이드 p14-v13-ar-limit — T 가 ref struct 일 수도 있으면, C# 13.0
using System;
using System.Collections.Generic;

#if FIELD
class Bag<T> where T : allows ref struct
{
    T item;                       // a class field lives on the heap
}
#endif

class App
{
    static int Use<T>(T t) where T : allows ref struct
    {
#if BOX
        object o = t;                 // boxing
#elif ARRAY
        var a = new T[1];             // array element
#elif LAMBDA
        Func<T> f = () => t;          // captured by a closure
#elif LIST
        var l = new List<T>();        // List<T> has no anti-constraint
#elif TOSTR
        string s = t.ToString();      // object method on T
        Console.WriteLine(s);
#endif
        return 1;
    }

    static void Main()
    {
        Console.WriteLine(Use(new Span<int>(new int[2])));
        Console.WriteLine(Use(5));
    }
}
