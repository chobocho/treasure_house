// 슬라이드 p6-v5-after-ref — async 안의 Span 지역 변수, C# 13.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> SumAsync(int[] data)
    {
        int total = 0;
        {
            // A ref struct local: fine as long as no await sees it.
            Span<int> head = data.AsSpan(0, 2);
            foreach (int x in head) total += x;
        }
        await Task.Yield();
        return total;
    }

    static async Task Main()
    {
        Console.WriteLine(await SumAsync(new[] { 3, 4, 5 }));
    }
}
