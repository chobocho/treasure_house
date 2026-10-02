// 슬라이드 p8-v7-tuple-linq — 익명 형식 대신 튜플, C# 7.0
using System;
using System.Linq;

class App
{
    static void Main()
    {
        string[] words = { "tuple", "is", "a", "struct" };
        var anon = words.Select(w => new { w, w.Length }); // inferred
        var tup = words.Select(w => (word: w, len: w.Length));
        Console.WriteLine(anon.First().Length + " " + tup.First().len);
        Console.WriteLine(anon.First());
        Console.WriteLine(tup.First());
        Console.WriteLine(anon.First().GetType().IsValueType + " "
            + tup.First().GetType().IsValueType);
        var plain = words.Select(w => (w, w.Length));
        Console.WriteLine(plain.First().Item2);
#if BAD
        Console.WriteLine(plain.First().Length);    // inferred name
#endif
    }
}
