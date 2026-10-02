// 슬라이드 p8-v7-locfn-async — async 의 인수 검사를 즉시, C# 7.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> Late(string s)
    {
        if (s == null) throw new ArgumentNullException(nameof(s));
        await Task.Yield();
        return s.Length;
    }

    static Task<int> Early(string s)
    {
        if (s == null) throw new ArgumentNullException(nameof(s));
        return Impl();

        async Task<int> Impl()
        {
            await Task.Yield();
            return s.Length;
        }
    }

    static void Try(string name, Func<string, Task<int>> f)
    {
        Task<int> t = null;
        try { t = f(null); }
        catch (ArgumentNullException) { }
        Console.WriteLine(name + ": call " + (t == null ? "threw"
            : "returned a task, faulted=" + t.IsFaulted));
        if (t == null) return;
        try { t.Wait(); }
        catch (AggregateException e)
        {
            Console.WriteLine(name + ": Wait threw "
                + e.InnerException.GetType().Name);
        }
    }

    static void Main()
    {
        Try("Late", Late);
        Try("Early", Early);
    }
}
