// 슬라이드 p8-v7-throw-lambda — 람다 본문의 throw 식, C# 7.0
using System;

class App
{
    static void Main()
    {
        Func<int, int> half = n =>
            n % 2 == 0 ? n / 2 : throw new ArgumentException("odd");
        Func<string> todo = () => throw new NotImplementedException();
        Action stop = () => throw new OperationCanceledException();

        Console.WriteLine(half(8));
        foreach (Delegate d in new Delegate[] { todo, stop })
        {
            try { d.DynamicInvoke(); }
            catch (System.Reflection.TargetInvocationException e)
            {
                Console.WriteLine(e.InnerException.GetType().Name);
            }
        }
#if BAD
        var f = () => throw new Exception();   // C# 10 natural type
#endif
    }
}
