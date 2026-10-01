// 슬라이드 p3-v2-iterator-object — 열거 가능 객체이자 열거자, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Seq()
    {
        yield return 1;
        yield return 2;
    }

    static void Main()
    {
        IEnumerable<int> s = Seq();
        IEnumerator<int> e1 = s.GetEnumerator();
        IEnumerator<int> e2 = s.GetEnumerator();
        Console.WriteLine(object.ReferenceEquals(s, e1));
        Console.WriteLine(object.ReferenceEquals(s, e2));
        e1.MoveNext();
        e2.MoveNext();
        e2.MoveNext();
        Console.WriteLine(e1.Current + " " + e2.Current);
    }
}
