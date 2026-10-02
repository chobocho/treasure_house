// 슬라이드 p8-v7_3-overload — 오버로드 후보를 미리 거르기, C# 7.3
using System;

class App
{
    // rule 1: static vs instance
    static void M(object o) { Console.WriteLine("static M(object)"); }
    void M(string s)        { Console.WriteLine("instance M(string)"); }

    // rule 2: a generic method whose constraint fails
    static void G<T>(T t) where T : struct
                            { Console.WriteLine("G<T>(T)"); }
    static void G(object o) { Console.WriteLine("G(object)"); }

    // rule 3: a method group whose return type does not fit
    static void K(string x) { }
    static int K(object x)  { return 3; }

    static void Main()
    {
        M("x");                    // no instance here
        G("s");                    // string is not a struct
        Func<string, int> f = K;   // must return int
        Console.WriteLine("K(object) -> " + f("k"));
    }
}
