// 슬라이드 p10-v9-static-lambda — static 익명 함수, C# 9.0
using System;

class App
{
    static int counter = 10;
    public int inst = 1;

    void Run()
    {
        const int k = 2;
        int local = 3;
        Func<int, int> f = static x => x * k + counter;   // ok
        Func<string> g = static () => nameof(local);      // ok
        Func<int, int> h = static delegate (int x) { return -x; };
        Console.WriteLine(f(5) + " " + g() + " " + h(local));
#if BAD
        Func<int> b1 = static () => local;                 // a local
        Func<int> b2 = static () => inst;                  // this
#endif
    }

    static void Main() => new App().Run();
}
