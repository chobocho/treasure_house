// 슬라이드 p10-v9-extenum-async — 확장 GetAsyncEnumerator, C# 9.0
using System;
using System.Collections.Generic;
using System.Threading.Channels;
using System.Threading.Tasks;

static class ChannelExt
{
    public static IAsyncEnumerator<T> GetAsyncEnumerator<T>(
        this ChannelReader<T> reader)
        => reader.ReadAllAsync().GetAsyncEnumerator();
}

class App
{
    static async Task Main()
    {
        Channel<string> ch = Channel.CreateUnbounded<string>();
        foreach (string s in new[] { "a", "b", "c" })
            ch.Writer.TryWrite(s);
        ch.Writer.Complete();

        await foreach (string s in ch.Reader)       // the reader itself
            Console.Write(s + " ");
        Console.WriteLine();
    }
}
