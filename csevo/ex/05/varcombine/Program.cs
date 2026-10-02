// 슬라이드 p5-v4-var-combine — 변성으로 담은 대리자를 합치면, C# 4.0
using System;

class Program
{
    static void Main()
    {
        Action<object> any = delegate(object o) {
            Console.WriteLine("any " + o); };
        Action<string> one = delegate(string s) {
            Console.WriteLine("str " + s); };
        Action<string> viaVariance = any;   // still an Action<object>
        Console.WriteLine(viaVariance.GetType());
        Action<string> same = one + one;
        same("ok");
        Action<string> mixed = one + viaVariance;  // differ at run time
        mixed("boom");
    }
}
