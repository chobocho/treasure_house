// 슬라이드 p9-v8-ud-goto — 제안서의 goto 예제, C# 8.0
using System;

class Res : IDisposable
{
    public void Dispose() => Console.WriteLine("dispose");
}

class App
{
    static void Main(string[] args)
    {
        using var first = new Res();
    target:
        using var second = new Res();
        if (args.Length > 0)
            goto target;             // the proposal: "disposes second"
    }
}
