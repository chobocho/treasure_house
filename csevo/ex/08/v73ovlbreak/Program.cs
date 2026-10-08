// 슬라이드 p8-v7_3-overload-rules — 7.3 에서 모호해진 호출, C# 7.2
using System;

class App
{
    static int M(object o) => 1;
    int M(string s) => 2;          // 인스턴스 멤버

    static void Run(Func<int, int> f) =>
        Console.WriteLine("Run(Func<int, int>)");
    static void Run(Func<string, int> f) =>
        Console.WriteLine("Run(Func<string, int>)");

    static void Main()
    {
        // 7.2 에서는 컴파일되어 한쪽을 부르고, 7.3 에서는 모호하다
        Run(x => M(x));
    }
}
