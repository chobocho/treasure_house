// 슬라이드 p9-v8-sl-meta — 대리자로 바꾼 지역 함수의 정체, C# 8.0
using System;

class App
{
    static void Show(string label, Func<int, int> f) =>
        Console.WriteLine("{0,-8} static={1,-5} type={2} target={3}",
            label, f.Method.IsStatic, f.Method.DeclaringType.Name,
            f.Target == null ? "null" : f.Target.GetType().Name);

    static void Main()
    {
        int k = 10;
        int Plain(int x) => x + 1;            // captures nothing
        static int Static(int x) => x + 1;
        int Capture(int x) => x + k;          // captures k

        Show("plain", Plain);
        Show("static", Static);
        Show("capture", Capture);
        Show("lambda", x => x + 1);
    }
}
