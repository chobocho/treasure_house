// 슬라이드 p6-v5-asyncvoid — async void 의 예외, C# 5.0
using System;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static async void Fire()
    {
        await Task.FromResult(0);
        throw new InvalidOperationException("from async void");
    }

    static void Main()
    {
        try
        {
            Fire();                     // no Task to hold on to
            Console.WriteLine("Main: Fire returned normally");
        }
        catch (Exception)
        {
            Console.WriteLine("Main: caught");  // never printed
        }
        Thread.Sleep(5000);
        Console.WriteLine("Main: not reached");
    }
}
