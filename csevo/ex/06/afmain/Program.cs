// 슬라이드 p6-v5-after-main — async Task<int> Main 과 진입점, C# 7.1
using System;
using System.Reflection;
using System.Threading.Tasks;

class App
{
    static async Task<int> Main(string[] args)
    {
        await Task.Yield();
        Console.WriteLine("args: " + string.Join(",", args));

        // The real entry point is a method the compiler adds.
        MethodInfo ep = Assembly.GetEntryAssembly().EntryPoint;
        Console.WriteLine("entry point: " + ep.Name
            + " returns " + ep.ReturnType.Name);
        return args.Length;     // becomes the exit code
    }
}
