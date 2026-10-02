// 슬라이드 p9-v8-shadow — 중첩 함수의 이름 가리기, C# 8.0
using System;

class App
{
    static void Main()
    {
        int x = 1;
        string name = "outer";

        Func<int, int> twice = x => x * 2;       // lambda x hides x
        Console.WriteLine(twice(10) + " " + x);

        Console.WriteLine(Greet("inner") + " " + name);
        static string Greet(string name)         // hides name
        {
            int x = name.Length;                 // hides x too
            return "hi " + name + " " + x;
        }
#if BAD
        { int x = 5; Console.WriteLine(x); }  // a block, not a fn
#endif
    }
}
