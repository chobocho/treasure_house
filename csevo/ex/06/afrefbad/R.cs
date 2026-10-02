// 슬라이드 p6-v5-after-ref — await 를 건너는 Span 은 안 된다, C# 13.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> SumAsync(int[] data)
    {
        Span<int> head = data.AsSpan(0, 2);
        await Task.Yield();
        return head[0] + head[1];
    }

    static void Main() { }
}
