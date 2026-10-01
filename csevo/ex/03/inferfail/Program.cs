// 슬라이드 p3-v2-inference-fail — 형식 유추가 못 하는 것, C# 2.0
using System;

class App
{
    static T Make<T>() { return default(T); }
    static T Pick<T>(T a, T b) { return a; }
    static void Show<T>(T x) { Console.WriteLine(x); }

    static void Main()
    {
        int n = Make();                   // the return type is not used
        Show(null);                       // null has no type
        object o = Pick(1, "a");          // int or string?
        Console.WriteLine(n + " " + o);
    }
}
