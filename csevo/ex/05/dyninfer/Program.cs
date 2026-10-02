// 슬라이드 p5-v4-dyn-infer — 형식 유추는 object 보다 dynamic, C# 4.0
using System;

class Program
{
    static void Main()
    {
        object o = "object";
        dynamic d = "dynamic";
        var arr = new[] { o, d };         // dynamic[]
        var pick = DateTime.MinValue.Year > 0 ? o : d;   // dynamic
        Console.WriteLine(arr[0].Length); // element is dynamic
        Console.WriteLine(pick.Length);
        Console.WriteLine(arr.GetType());
#if BAD
        object[] plain = new[] { o, o };
        string s = plain[0];
#endif
    }
}
