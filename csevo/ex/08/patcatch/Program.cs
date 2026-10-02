// 슬라이드 p8-v7-pat-catch — 예외 필터 안의 패턴 변수, C# 7.0
using System;

class App
{
    static void Run(Action a)
    {
        try { a(); }
        catch (Exception e) when (e is ArgumentException ae
                                  && ae.ParamName == "id")
        {
            Console.WriteLine("bad id: " + ae.GetType().Name);
        }
        catch (Exception e)
        {
            Console.WriteLine("other: " + e.GetType().Name);
        }
    }

    static void Main()
    {
        Run(() => throw new ArgumentNullException("id"));
        Run(() => throw new ArgumentException("x", "name"));
        Run(() => throw new InvalidOperationException());
    }
}
